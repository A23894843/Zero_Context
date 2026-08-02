#include <iostream>
#include <fcntl.h>
#include <unistd.h>
#include <sys/socket.h>
#include <sys/un.h>
#include <chrono>
#include <filesystem>
#include <string>
using namespace std;

const char* MOUSE_DEVICE = "/dev/input/mice";
string UDS_PATH = (filesystem::current_path() / "Zero_Context_mouse.sock").string();

int main () {
    int sock = socket(AF_UNIX, SOCK_STREAM, 0);
    struct sockaddr_un addr;
    addr.sun_family = AF_UNIX;
    strncpy(addr.sun_path, UDS_PATH.c_str(), sizeof(addr.sun_path) - 1);
    addr.sun_path[sizeof(addr.sun_path) - 1] = '\0';

    if (connect(sock, (struct sockaddr*)&addr, sizeof(addr)) == -1) {
        cerr << "[!] Python backend not running. Start server_core.py first.\n";
        return 1;
    }

    cout << "[*] Connected to Python Backend IPC.\n";

    int fd = open (MOUSE_DEVICE, O_RDONLY);
    if (fd == -1)   {
        cerr << "[!] Failed to open " << MOUSE_DEVICE << ". Run with sudo!\n";
        return 1;
    }
    cout << "[*] C++ Hardware Hook Active. Streaming kinematics...\n";

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
    return 0;
}