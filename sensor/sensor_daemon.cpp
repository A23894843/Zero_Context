#include <iostream>
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
const char* KBD_DEVICE = "/dev/input/event0";
string UDS_MOUSE = (filesystem::current_path() / "Zero_Context_mouse.sock").string();
string UDS_KBD = (filesystem::current_path() / "Zero_Context_kbd.sock").string();

int connect_uds (const char* path) {
    int sock = socket(AF_UNIX, SOCK_STREAM, 0);
    struct sockaddr_un addr;
    addr.sun_family = AF_UNIX;
    strncpy(addr.sun_path, path, sizeof(addr.sun_path) - 1);
    addr.sun_path[sizeof(addr.sun_path) - 1] = '\0';

    while (connect(sock, (struct sockaddr*)&addr, sizeof(addr)) == -1) {
        this_thread :: sleep_for (chrono :: milliseconds (100));
    }   return sock;
}

double get_timestamp() {
    auto now = chrono :: system_clock :: now();
    return chrono :: duration <double> (now.time_since_epoch()).count();
}

void stream_mouse() {
    int sock = connect_uds(UDS_MOUSE.c_str());
    int fd = open (MOUSE_DEVICE, O_RDONLY);
    if (fd == -1)   {
        cerr << "[!] Failed to open " << MOUSE_DEVICE << ". Run with sudo!\n";
        return;
    }

    unsigned char data [3];
    while (read(fd, data, sizeof(data)) > 0)    {
        int dx = (char) data [1];
        int dy = (char) data [2];

        if (dx != 0 || dy != 0) {
            auto now = chrono::system_clock::now();
            auto duration = now.time_since_epoch();
            double timestamp = chrono::duration <double> (duration).count();

            string payload = "{\"dx\": " + to_string(dx) + 
                            ", \"dy\": " + to_string(dy) + 
                            ", \"timestamp\": " + to_string(timestamp) + "}\n";

            send (sock, payload.c_str(), payload.length(), 0);
        }
    }   close (fd);
    close (sock);
}

void stream_keyboard() {
    int sock = connect_uds(UDS_KBD.c_str());
    int fd = open (KBD_DEVICE, O_RDONLY);
    if (fd == -1)   {
        cerr << "[!] Failed to open " << KBD_DEVICE << ". Run with sudo!\n";
        return;
    }
    
    struct input_event ev;
    while (read(fd, &ev, sizeof(struct input_event)) > 0)    {

        if (ev.type == 1 && (ev.value == 0 || ev.value == 1)) {
            string payload = "{\"key_code\": " + to_string(ev.code) + 
                            ", \"state\": " + to_string(ev.value) + 
                            ", \"timestamp\": " + to_string(get_timestamp()) + "}\n";

            send (sock, payload.c_str(), payload.length(), 0);
        }
    }   close (fd);
    close (sock);
}

int main () {
    thread mouse_thread (stream_mouse);
    thread kbd_thread (stream_keyboard);

    mouse_thread.join();
    kbd_thread.join();

    return 0;
}