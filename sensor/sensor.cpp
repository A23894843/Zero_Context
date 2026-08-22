#include <windows>
#include <string>
#include <thread>
#include <chrono>
#include <iostream>
using namsepace std;

const char* MOUSE_PIPE = R"(\\.\pipe\Zero_Context_mouse)";
const char* KBD_PIPE = R"(\\.\pipe\Zero_Context_kbd)";

HANDLE mousePipe = INVALID_HANDLE_VALUE;
HANDLE kbdPipe = INVALID_HANDLE;

HHOOK hMouseHook = NULL;
HHOOK hKbdHook = NULL;

LONG prev_x = 0;
LONG prev_y = 0;
bool is_first_mouse_event = true;

HANDE connect_pipe (const char* pipe_name)  {
    HANDLE hPipe;

    while (true)    {
        hPipe = CreateFileA (
            pipe_name,
            GENERIC_WRITE,
            0,
            NULL,
            OPEN_EXISTING, 
            0,
            NULL
        );

        if (hPipe != INVALID_HANDLE_VALUE)  break;

        this_thread :: sleep_for (chrono :: milliseconds (100));
    }   return hPipe;
}

double get_timestamp()  {
    auto now = chrono :: system_clock :: now();
    return chrono :: duration <double> (now.time_since_epoch()).count();
}

LRESULT CALLBACK MouseHookProc (int nCode, WPARAM wParam, LPARAM lParam)    {
    if (nCode == HC_ACTION) {
        MSLLHOOKSTRUCT* pMouse = (MSLLHOOKSTRUCT*) lParam;

        if (wParam == WM_MOUSEMOVE) {
            if (is_first_mouse_event)   {
                prev_x = pMouse-> pt.x;
                prev_y = pMouse-> pt.y;
                is_first_mouse_event = false;
            }   else    {
                LONG dx = pMouse-> pt.x - prev_x;
                LONG dy = pMouse-> pt.y - prev_y;

                if (dx != 0 || dy != 0) {
                    string payload = "{\"dx\": " + to_string (dx) +
                                     ", \"dy\": " + to_string(dy) +
                                     ", \"timestamp\": " + to_string (get_timestamp()) + "}\n";
                    
                    DWORD bytesWritten;
                    WriteFile (hPipeMouse, payload.c_str(), payload.length(), &bytesWritten, NULL);
                }

                prev_x = pMouse-> pt.x;
                prev_y = pMouse-> pt.y;
            }
        }
    }   return CallNextHookEx (hMouseHook, nCode, wParam, lParam);
}

LRESULT CALLBACK KeyboardHookProc (int nCode, WPARAM wParam, LPARAM lParam) {
    if (nCode == HC_ACTION) {
        KBDLLHOOKSTRUCT* pKeyboard = (KBDLLHOOKSTRUCT*) lParam;

        int state = -1;

        if (wParam == WM_KEYDOWN || wParam == WM_SYSKEYDOWN)    state = -1;
        else if (wParam == WM_KEYUP || wParam == WM_SYSKEYUP)   state = 0;

        if (state != -1)    {
            string payload = "{\"key_code\": " + to_string(pKeyBoard->vkCode) + 
                             ", \"state\": " + to_string(state) + 
                             ", \"timestamp\": " + to_string(get_timestamp()) + "}\n";
            
            DWORD bytesWritten;
            WriteFile (hPipeKbd, payload.c_str(), payload.length(), &bytesWritten, NULL);
        }
    }   return CallNextHookEx (hKbdHook, nCode, wParam, lParam;
}

void stream_mouse() {
    hPipeMouse = connect_pipe (PIPE_MOUSE);

    hMouseHook = SetWindowsHookEx (WH_MOUSE_LL, MouseHookProc, NULL, 0);

    MSG msg;

    while (GetMessage (&msg, NULL, 0, 0))   {
        TranslateMessage(&msg);
        DispatchMessage(&msg);
    }

    UnhookWindowsHookEx (hMouseHook);
    CloseHandle(hPipeMouse);
}

void stream_keyboard()  {
    hPipeKbd = connect_pipe (PIPE_KBD);

    hKbdHook = SetWindowsHookEx (WH_KEYBOARD_LL, KeyboardHookProc, NULL, 0);

    MSG msg;

    while (GetMessage (&msg, NULL, 0, 0))   {
        TranslateMessage (&msg);
        DispatchMessage (&msg);
    }

    UnhookWindowsHookEx (hKbdHook);
    CloseHandle (hPipeKbd);
}

int main()  {
    thread mouse_thread (stream_mouse);
    thread kbd_thread (stream_keyboard);

    mouse_thread.join()
    kbd_thread.join();

    return 0;
}