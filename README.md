# <img src='./logo.svg' card_color="#FF8600" width="50" style="vertical-align:bottom" style="vertical-align:bottom">Launcher

Skill used to launch programs and navigate websites

## Requirements

`neon-utils`

## Description

This example skill is used to launch desktop applications and browse web pages.

## Examples

- "Browse to neon.ai"
- "Navigate to google.com"
- "Open notepad."
- "Launch terminal."

## Location

    ${skills}/launcher.neon

## Files

    launcher.neon/vocab
    launcher.neon/vocab/en-us
    launcher.neon/vocab/en-us/program.entity
    launcher.neon/vocab/en-us/launch.intent
    launcher.neon/README.md
    launcher.neon/regex
    launcher.neon/regex/en-us
    launcher.neon/regex/en-us/Program.rx
    launcher.neon/__init__.py
    launcher.neon/LauncherSkill.yml
    launcher.neon/dialog
    launcher.neon/dialog/en-us
    launcher.neon/dialog/en-us/LaunchProgram.dialog
    launcher.neon/dialog/en-us/NotFound.dialog
  

## Class Diagram

[Click here](https://0000.us/klatchat/app/files/neon_images/class_diagrams/personal.png)

## Available Intents
<details>
<summary>Click to expand.</summary>
<br>

### launch.intent  

    (launch|lunch|open) {program}
      
### program.entity
 
    chrome
    chromium
    browser
    nautilus
    files
    file explorer
    terminal
    gnome terminal
    command line
    gedit
    g edit
    text edit
    text editor
    notepad 

</details>

## Details

### Text

        Launch Chrome
        >> My name is Neon. I am an artificial intelligence personal assistant augmented with Neon Gecko dot com Inc copyrighted code and CPI Corp patented technology.

### Picture

### Video

  

## Contact Support

Use the [link](https://neongecko.com/ContactUs) or [submit an issue on GitHub](https://help.github.com/en/articles/creating-an-issue)

## Credits
[NeonGeckoCom](https://github.com/NeonGeckoCom)
[NeonDaniel](https://github.com/NeonDaniel)
[reginaneon](https://github.com/reginaneon)

## Category
**Productivity**
Daily

## Tags
#NeonGecko Original
#NeonAI
#browser
#desktop
#web