# NEON AI (TM) SOFTWARE, Software Development Kit & Application Framework
# All trademark and other rights reserved by their respective owners
# Copyright 2008-2022 Neongecko.com Inc.
# Contributors: Daniel McKnight, Guy Daniels, Elon Gasper, Richard Leeds,
# Regina Bloomstine, Casimiro Ferreira, Andrii Pernatii, Kirill Hrymailo
# BSD-3 License
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions are met:
# 1. Redistributions of source code must retain the above copyright notice,
#    this list of conditions and the following disclaimer.
# 2. Redistributions in binary form must reproduce the above copyright notice,
#    this list of conditions and the following disclaimer in the documentation
#    and/or other materials provided with the distribution.
# 3. Neither the name of the copyright holder nor the names of its
#    contributors may be used to endorse or promote products derived from this
#    software without specific prior written permission.
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS"
# AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO,
# THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR
# PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT HOLDER OR
# CONTRIBUTORS  BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL,
# EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO,
# PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA,
# OR PROFITS;  OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF
# LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING
# NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS
# SOFTWARE,  EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.

import difflib
import re
import subprocess
import webbrowser

from adapt.intent import IntentBuilder
from mycroft_bus_client import Message
from neon_utils.message_utils import request_from_mobile
from neon_utils.skills.neon_skill import NeonSkill, LOG
from ovos_utils.gui import is_gui_installed


class LauncherSkill(NeonSkill):
    def __init__(self):
        super(LauncherSkill, self).__init__(name="LauncherSkill")
        self.chromium_opts = ['chrome', 'chromium', 'browser']
        self.nautilus_opts = ['nautilus', 'files', 'file explorer']
        self.terminal_opts = ['terminal', 'gnome terminal', 'command line']
        self.textedit_opts = ['gedit', 'g edit', 'text edit', 'text editor', 'notepad', 'textedit']
        self.valid_domains = ('com', 'net', 'org', 'edu', 'gov', 'ai', 'us', 'tech')

    def initialize(self):
        browse_website_intent = IntentBuilder("browse_website_intent").require("BrowseKeyword"). \
            require("website").optionally("Neon").build()
        self.register_intent(browse_website_intent, self.browse_website_intent)
        self.register_entity_file("program.entity")
        self.register_intent_file("launch.intent", self.launch_program_intent)

    def launch_program_intent(self, message):
        if self.neon_in_request(message):
            if message.context.get("mobile"):
                self.speak_dialog("MobileNotSupported", private=True)
            elif message.context.get('klat_data'):
                pass
            else:
                LOG.debug(message.data)
                program = message.data.get('program')
                LOG.debug(program)

                if program in self.chromium_opts:
                    # self.speak("Launching Chrome.")
                    # program = "Chrome"
                    # TODO: Check for app, try Google Chrome?
                    subprocess.Popen(["chromium-browser", "https://neongecko.com/"],
                                     stdout=subprocess.PIPE, stdin=subprocess.PIPE, stderr=subprocess.PIPE)
                elif program in self.nautilus_opts:
                    # self.speak("Launching File Explorer.")
                    # program = "File Explorer"
                    subprocess.Popen(["nautilus"],
                                     stdout=subprocess.PIPE, stdin=subprocess.PIPE, stderr=subprocess.PIPE)
                elif program in self.terminal_opts:
                    # self.speak("Launching Terminal.")
                    # program = "Terminal"
                    subprocess.Popen(["gnome-terminal"],
                                     stdout=subprocess.PIPE, stdin=subprocess.PIPE, stderr=subprocess.PIPE)
                elif program in self.textedit_opts:
                    # program = "Text editor"
                    subprocess.Popen(["gedit"],
                                     stdout=subprocess.PIPE, stdin=subprocess.PIPE, stderr=subprocess.PIPE)
                else:
                    self.browse_website_intent(message)
                self.speak_dialog('LaunchProgram', {'program': program})
            # else:
            #     self.speak_dialog('NotFound', {'program': program})
            #     if program:
            #         self.speak_dialog('LaunchProgram', {'program': program})
            #     else:
            #         self.speak("I don't know that program")

    def browse_website_intent(self, message):
        # from NGI.utilities.utilHelper import scrape_page_for_links as scrape
        from neon_utils.web_utils import scrape_page_for_links as scrape
        LOG.debug(message.data)
        # website = message.data.get('website')
        if self.neon_in_request(message):
            website = message.data.get('utterance').split(" to ", 1)[1]
            LOG.debug(website)

            # Catch request for page on website
            if " on " in website:
                page, website = website.split(" on ")
            else:
                page = None
            LOG.debug(len(website.split()))

            # This either has no specified tld or had the '.' parsed out by stt
            if '.' not in website:
                if len(website.split()) == 1:  # No possible TLD to parse, assume .com
                    website = f"{website}.com"
                elif len(website.split()) == 2 and website.split()[1] in self.valid_domains:  # Try to match valid TLD
                    website = re.sub("\.\.", ".", ".".join(website.split()))
                else:
                    LOG.warning(f"Complicated website: {website}")
                    parts = website.split()
                    if parts[len(parts) - 1] in self.valid_domains:  # Assume last "word" is the TLD
                        website = f'{"".join(parts[0:(len(parts) - 1)])}.{parts[len(parts) - 1]}'
                    else:  # No possible TLD to parse, assume .com
                        website = f'{"".join(parts)}.com'
            elif not website.rsplit('.', 1)[1]:
                # TODO: Better parsing here DM
                if website.replace(" ", "") == "neon":
                    website = "https://neon.ai"
                else:
                    website = f"{website.replace(' ', '')}com"
            else:
                website = "".join(website.split()).strip('"')
            LOG.debug(f"Check website: {website}")
            links = scrape(website)
            LOG.debug(f"found links: {links}")

            # If we know this web address is valid
            if links == "Invalid Domain":
                self.speak_dialog("WebsiteNotFound", {"website": website}, private=True)
                # Tell user website not found (TODO: call search intent? try different subdomain? DM)
            else:
                if page and page in links.keys():
                    website = links[page]
                elif page:
                    LOG.debug(f"DM: Looking for {page} on {website}")
                    close_matches = difflib.get_close_matches(page, links.keys(), cutoff=0.5)
                    LOG.debug(close_matches)
                    if close_matches:
                        website = links[close_matches[0]]
                # TODO: Conditionally speak site name? DM
                self.speak_dialog("LaunchWebsite", {"website": website}, private=True)
                if request_from_mobile(message):
                    pass
                    # TODO
                    # self.mobile_skill_intent("web_browser", {"link": website}, message)
                    # self.socket_io_emit('web_browser', f"&link={website}", message.context["flac_filename"])
                elif message.data.get('klat_data'):
                    # TODO
                    self.bus.emit(Message('css.emit',
                                          {"event": "navigate to page",
                                           "data": [website, message.context[
                                               "klat_data"]["request_id"]]}))
                elif self.gui_enabled or is_gui_installed():
                    if not website.startswith("http"):
                        # TODO: use neon_utils here DM
                        website = f"https://{website}"
                    self.gui.show_url(website)
                else:
                    LOG.info(website)
                    if not website.startswith("http"):
                        # TODO: use neon_utils here DM
                        website = f"https://{website}"
                    webbrowser.open_new(website)

    def stop(self):
        if self.gui_enabled:
            self.gui.clear()


def create_skill():
    return LauncherSkill()
