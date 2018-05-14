import subprocess


class CommandRunner:
    def __init__(self, title):
        self.title = title
        self.baseScript = 'start powershell -NoProfile -Command "' \
                          '[console]::BackgroundColor=\'Black\'; ' \
                          '[console]::ForegroundColor=\'DarkGray\'; ' \
                          '[console]::Title=\'%s\'; ' \
                          '[console]::WindowWidth=90; ' \
                          '[console]::WindowHeight=20; ' \
                          '[console]::BufferWidth=' \
                          '[console]::WindowWidth; ' \
                          'Write-Host "Starting..." -ForegroundColor DarkGreen;' \
                          '"%s"; ' \
                          'Write-Host "Completed. Press any key to continue ..." ' \
                          '-ForegroundColor Green;' \
                          '$x=[console]::ReadKey()'

    def execute_wait(self, command):
        script = str(self.baseScript % (self.title, command))
        subprocess.Popen(script, shell=True).wait()

    def execute_async(self, command):
        script = str(self.baseScript % (self.title, command))
        subprocess.Popen(script, shell=True)
