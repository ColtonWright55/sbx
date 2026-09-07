import SwiftUI

@main
struct CjwlogGPSApp: App {
    @UIApplicationDelegateAdaptor(AppDelegate.self) var appDelegate

    var body: some Scene {
        WindowGroup {
            Text("cjwlog gps — logging in the background")
                .padding()
        }
    }
}
