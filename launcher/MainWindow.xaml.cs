using System;
using System.Diagnostics;
using System.IO;
using System.Windows;
using System.Windows.Controls;

namespace ShadowgridLauncher
{
    public partial class MainWindow : Window
    {
        public MainWindow()
        {
            InitializeComponent();
        }

        private void BtnStart_Click(object sender, RoutedEventArgs e)
        {
            string resolution = ((ComboBoxItem)ComboResolution.SelectedItem).Content.ToString();
            string monitor = ((ComboBoxItem)ComboMonitor.SelectedItem).Content.ToString();
            
            // Parse resolution (e.g., 1280x720)
            string[] resParts = resolution.Split('x');
            string width = resParts[0];
            string height = resParts[1];
            
            string displayIndex = monitor.Contains("2") ? "1" : "0";
            
            bool isFullscreen = ChkFullscreen.IsChecked ?? false;
            string fsArg = isFullscreen ? " --fullscreen" : "";

            string exePath = Path.Combine(AppDomain.CurrentDomain.BaseDirectory, "game", "Shadowgrid.exe");
            
            if (!File.Exists(exePath))
            {
                exePath = "python"; 
            }

            try
            {
                ProcessStartInfo startInfo = new ProcessStartInfo();
                if (exePath == "python") {
                    startInfo.FileName = "python";
                    startInfo.Arguments = $"-m src.main --width {width} --height {height} --display {displayIndex}{fsArg}";
                    startInfo.WorkingDirectory = Path.GetFullPath(Path.Combine(AppDomain.CurrentDomain.BaseDirectory, "..", "..", "..", ".."));
                } else {
                    startInfo.FileName = exePath;
                    startInfo.Arguments = $"--width {width} --height {height} --display {displayIndex}{fsArg}";
                    startInfo.WorkingDirectory = Path.Combine(AppDomain.CurrentDomain.BaseDirectory, "game");
                }
                
                startInfo.UseShellExecute = false;
                Process.Start(startInfo);
                Application.Current.Shutdown();
            }
            catch (Exception ex)
            {
                MessageBox.Show($"Failed to start game: {ex.Message}");
            }
        }
    }
}