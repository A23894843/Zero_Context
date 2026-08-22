#include <iostream>
#include <cstring>
#include <fcntl.h>
#include <unistd.h>
#include <sys/socket.h>
#include <sys/un.h>
#include <chrono>
#include <filesystem>
#include <string>
#include <thread>
#include <linux/input.h>
using namespace std;

const char* MOUSE_DEVICE = "/dev/input/mice";
string UDS_MOUSE = (filesystem::current_path() / "temporary" / "Zero_Context_mouse.sock").string();
string UDS_KBD = (filesystem::current_path() / "temporary" / "Zero_Context_kbd.sock").string();

// Opens a UDS connection, retrying until the Python server is listening.
int connect_uds(const char* path) {
    int sock = socket(AF_UNIX, SOCK_STREAM, 0);
    if (sock == -1) {
        cerr << "[!] Failed to create socket: " << strerror(errno) << "\n";
        return -1;
    }

    struct sockaddr_un addr;
    memset(&addr, 0, sizeof(addr));
    addr.sun_family = AF_UNIX;
    strncpy(addr.sun_path, path, sizeof(addr.sun_path) - 1);

    while (connect(sock, (struct sockaddr*)&addr, sizeof(addr)) == -1) {
        this_thread::sleep_for(chrono::milliseconds(100));
    }
    return sock;
}

// Sends the full payload, retrying on partial writes. Returns false if the
// socket has died (e.g. the Python server restarted), so the caller can
// reconnect instead of silently dropping every subsequent event.
bool send_all(int sock, const string& payload) {
    size_t total_sent = 0;
    while (total_sent < payload.size()) {
        ssize_t sent = send(sock, payload.c_str() + total_sent, payload.size() - total_sent, MSG_NOSIGNAL);
        if (sent <= 0) {
            cerr << "[!] IPC send failed: " << strerror(errno) << "\n";
            return false;
        }
        total_sent += static_cast<size_t>(sent);
    }
    return true;
}

double get_timestamp() {
    auto now = chrono::system_clock::now();
    return chrono::duration<double>(now.time_since_epoch()).count();
}

void stream_mouse() {
    int fd = open(MOUSE_DEVICE, O_RDONLY);
    if (fd == -1) {
        cerr << "[!] Failed to open " << MOUSE_DEVICE << ". Run with sudo!\n";
        return;
    }

    int sock = connect_uds(UDS_MOUSE.c_str());
    if (sock == -1) {
        close(fd);
        return;
    }

    unsigned char data[3];
    while (read(fd, data, sizeof(data)) > 0) {
        int dx = (char)data[1];
        int dy = (char)data[2];

        if (dx != 0 || dy != 0) {
            double timestamp = get_timestamp();

            string payload = "{\"dx\": " + to_string(dx) +
                            ", \"dy\": " + to_string(dy) +
                            ", \"timestamp\": " + to_string(timestamp) + "}\n";

            // If the write fails (server restarted, socket dropped), reconnect
            // instead of silently losing every event for the rest of the run.
            if (!send_all(sock, payload)) {
                close(sock);
                sock = connect_uds(UDS_MOUSE.c_str());
                if (sock == -1) break;
            }
        }
    }
    close(fd);
    if (sock != -1) close(sock);
}

void stream_keyboard(string kbd_device_path) {
    int fd = open(kbd_device_path.c_str(), O_RDONLY);
    if (fd == -1) {
        cerr << "[!] Failed to open " << kbd_device_path << ". Run with sudo!\n";
        return;
    }

    int sock = connect_uds(UDS_KBD.c_str());
    if (sock == -1) {
        close(fd);
        return;
    }

    struct input_event ev;
    while (read(fd, &ev, sizeof(struct input_event)) > 0) {
        if (ev.type == 1 && (ev.value == 0 || ev.value == 1)) {
            string payload = "{\"key_code\": " + to_string(ev.code) +
                            ", \"state\": " + to_string(ev.value) +
                            ", \"timestamp\": " + to_string(get_timestamp()) + "}\n";

            if (!send_all(sock, payload)) {
                close(sock);
                sock = connect_uds(UDS_KBD.c_str());
                if (sock == -1) break;
            }
        }
    }
    close(fd);
    if (sock != -1) close(sock);
}

int main(int argc, char* argv[]) {
    string kbd_path = "/dev/input/event0";

    if (argc > 1) kbd_path = argv[1];

    thread mouse_thread(stream_mouse);
    thread kbd_thread(stream_keyboard, kbd_path);

    mouse_thread.join();
    kbd_thread.join();

    return 0;
}
