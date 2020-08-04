# NEON AI (TM) SOFTWARE, Software Development Kit & Application Development System
#
# Copyright 2008-2020 Neongecko.com Inc. | All Rights Reserved
#
# Notice of License - Duplicating this Notice of License near the start of any file containing
# a derivative of this software is a condition of license for this software.
# Friendly Licensing:
# No charge, open source royalty free use of the Neon AI software source and object is offered for
# educational users, noncommercial enthusiasts, Public Benefit Corporations (and LLCs) and
# Social Purpose Corporations (and LLCs). Developers can contact developers@neon.ai
# For commercial licensing, distribution of derivative works or redistribution please contact licenses@neon.ai
# Distributed on an "AS IS” basis without warranties or conditions of any kind, either express or implied.
# Trademarks of Neongecko: Neon AI(TM), Neon Assist (TM), Neon Communicator(TM), Klat(TM)
# Authors: Guy Daniels, Daniel McKnight, Regina Bloomstine, Elon Gasper, Richard Leeds
#
# Specialized conversational reconveyance options from Conversation Processing Intelligence Corp.
# US Patents 2008-2020: US7424516, US20140161250, US20140177813, US8638908, US8068604, US8553852, US10530923, US10530924
# China Patent: CN102017585  -  Europe Patent: EU2156652  -  Patents Pending

import difflib
import re
import subprocess
from mycroft.skills.core import MycroftSkill
from mycroft.util.log import LOG
from adapt.intent import IntentBuilder


class LauncherSkill(MycroftSkill):
    def __init__(self):
        super(LauncherSkill, self).__init__(name="LauncherSkill")
        self.chromium_opts = ['chrome', 'chromium', 'browser']
        self.nautilus_opts = ['nautilus', 'files', 'file explorer']
        self.terminal_opts = ['terminal', 'gnome terminal', 'command line']
        self.textedit_opts = ['gedit', 'g edit', 'text edit', 'text editor', 'notepad']
        self.valid_domains = ('com', 'net', 'org', 'edu', 'gov', 'ai', 'us', 'tech')

    def initialize(self):
        launch_program_intent = IntentBuilder("launch_program_intent").require("LaunchKeyword"). \
            require('program').optionally("Neon").build()
        self.register_intent(launch_program_intent, self.launch_program_intent)
        browse_website_intent = IntentBuilder("browse_website_intent").require("BrowseKeyword"). \
            require("website").optionally("Neon").build()
        self.register_intent(browse_website_intent, self.browse_website_intent)
        # self.register_entity_file("program.entity")
        # self.register_intent_file("launch.intent", self.launch_program_intent)

    def launch_program_intent(self, message):
        if self.neon_in_request(message):
            LOG.debug(message.data)
            program = message.data.get('program')
            LOG.debug(program)

            if program in self.chromium_opts:
                # self.speak("Launching Chrome.")
                # program = "Chrome"
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
            self.speak_dialog('LaunchProgram', {'program': program})
            # else:
            #     self.speak_dialog('NotFound', {'program': program})
            #     if program:
            #         self.speak_dialog('LaunchProgram', {'program': program})
            #     else:
            #         self.speak("I don't know that program")

    def browse_website_intent(self, message):
        from NGI.utilities.utilHelper import scrape_page_for_links as scrape
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
                if len(website.split()) == 1:
                    website = f"{website}.com"
                elif len(website.split()) == 2 and website.split()[1] in self.valid_domains:
                    website = re.sub("\.\.", ".", ".".join(website.split()))
                else:
                    LOG.warning(f"Complicated website: {website}")
                    parts = website.split()
                    if parts[len(parts) - 1] in self.valid_domains:
                        website = f'{"".join(parts[0:(len(parts) - 1)])}.{parts[len(parts) - 1]}'
                    else:
                        website = f'{"".join(parts)}.com'
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
                if message.context["mobile"]:
                    self.socket_io_emit('web_browser', f"&link={website}", message.context["flac_filename"])
                elif self.server:
                    self.socket_io_emit(event="navigate to page", message=website,
                                        flac_filename=message.context["flac_filename"])
                elif self.gui_enabled:
                    # TODO: Better parsing here DM
                    self.gui.show_url(website)
                else:
                    LOG.info(website)
                    subprocess.Popen(["chromium-browser", website],
                                     stdout=subprocess.PIPE, stdin=subprocess.PIPE, stderr=subprocess.PIPE)
        # else:
        #     self.check_for_signal("CORE_andCase")

    def stop(self):
        pass


def create_skill():
    return LauncherSkill()
