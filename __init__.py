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
import webbrowser
from typing import Optional

import requests
from ovos_bus_client import Message
from ovos_utils import classproperty
from ovos_utils.process_utils import RuntimeRequirements
from ovos_utils.log import LOG
from ovos_utils.gui import is_gui_installed
from neon_utils.message_utils import request_from_mobile
from neon_utils.skills.neon_skill import NeonSkill
from neon_utils.web_utils import scrape_page_for_links as scrape
from ovos_workshop.decorators import intent_handler
from ovos_workshop.intents import IntentBuilder


class LauncherSkill(NeonSkill):
    def __init__(self, **kwargs):
        NeonSkill.__init__(self, **kwargs)
        self.valid_domains = ('com', 'net', 'org', 'edu', 'gov', 'ai', 'us',
                              'tech')

    @classproperty
    def runtime_requirements(self):
        return RuntimeRequirements(network_before_load=False,
                                   internet_before_load=False,
                                   gui_before_load=False,
                                   requires_internet=True,
                                   requires_network=True,
                                   requires_gui=True,
                                   no_internet_fallback=False,
                                   no_network_fallback=False,
                                   no_gui_fallback=False)

    @intent_handler("launch_program.intent")
    def handle_launch_program(self, message):
        """
        Handle a request to launch a specific program
        """
        if not self.neon_in_request(message):
            return
        if message.context.get("mobile"):
            self.speak_dialog("mobile_not_supported", private=True)
        elif message.context.get('klat_data'):
            pass
        else:
            LOG.debug(message.data)
            program = message.data.get('program')
            LOG.debug(program)
            self.speak_dialog("not_supported", private=True)

    @intent_handler(IntentBuilder("BrowseWebsiteIntent")
                    .require("browse").require("website").build())
    def handle_browse_website(self, message):
        LOG.debug(message.data)
        if not self.neon_in_request(message):
            return

        website = message.data.get('website')
        LOG.debug(website)

        # Catch request for page on website
        page, website = self._parse_page_in_request(website)

        website = self._parse_url_from_website(website)
        LOG.debug(f"Check website: {website}")

        url = self._validate_url(website)
        if not url:
            self.speak_dialog("website_not_found", {"website": website},
                              private=True)
            # TODO: call search intent? try different subdomain? DM
            return

        links = scrape(website)
        LOG.debug(f"found links: {links}")

        if page and page in links.keys():
            website = links[page]
            LOG.debug(f"Found requested page: {website}")
        elif page:
            LOG.debug(f"Looking for {page} on {website}")
            close_matches = difflib.get_close_matches(page,
                                                      links.keys(), cutoff=0.5)
            if close_matches:
                LOG.debug(close_matches)
                website = links[close_matches[0]]
                LOG.debug(f"Found requested page: {website}")

        # TODO: Conditionally speak site name? DM
        self.speak_dialog("launch_website", {"website": website}, private=True)
        if request_from_mobile(message):
            pass
            # TODO
        elif message.data.get('klat_data'):
            self.bus.emit(Message('css.emit',
                                  {"event": "navigate to page",
                                   "data": [website, message.context[
                                       "klat_data"]["request_id"]]}))
        elif self.gui_enabled or is_gui_installed():
            self.gui.show_url(website)
        else:
            webbrowser.open_new(website)

    def _parse_page_in_request(self, website: str) -> (Optional[str], str):
        """
        Split a requested page from a website request.
        :param website: Parsed website request from user
        :returns: Optionally parsed page, requested website
        """
        website_parts = website.split()
        if len(website_parts) == 1:
            return None, website
        on_word = self.translate('on')
        if on_word in website_parts:
            on_idx = website_parts.index(on_word)
            page = " ".join(website_parts[:on_idx])
            website = " ".join(website_parts[on_idx + 1:])
            LOG.debug(f"{page} | {website}")
            return page, website
        return None, website

    def _parse_url_from_website(self, website: str) -> str:
        """
        Parse a spoken website request into a navigable string
        :param website: Parsed website request from user (with no pages)
        """
        dot = self.translate('dot')
        if dot in website.split():
            website = " ".join([p if p != dot else '.'
                                for p in website.split()])

        if '.' in website:
            if website.endswith('.'):
                LOG.info("Website ends with '.', assume .com")
                return f"{website.replace(' ', '')}com"
            else:
                LOG.debug(f"Returning: {website}")
                return website.replace(' ', '')

        if len(website.split()) == 1:
            LOG.warning(f"No TLD in one-word website: {website}")
            if website == "neon":
                return "neon.ai"
            else:
                LOG.debug(f"Assuming .com")
                return f"{website}.com"

        parts = website.split()
        if parts[-1] in self.valid_domains:
            website = "".join(parts[:-1]) + f'.{parts[-1]}'
            LOG.debug(f"Returning {website}")
            return website

        LOG.warning(f"Assuming .com")
        return f"{website.replace(' ', '')}.com"

    @staticmethod
    def _validate_url(url: str) -> Optional[str]:
        """
        Ensure a parsed URL is valid and return validated URL with schema.
        :param url: string URL to validate
        :returns: validated URL with schema or None
        """
        try:
            if url.startswith("http"):
                test = requests.get(url)
                if test.ok:
                    return url
            https_url = f'https://{url}'
            test = requests.get(https_url)
            if test.ok:
                return https_url
            http_url = f'http://{url}'
            test = requests.get(http_url)
            if test.ok:
                return http_url
        except Exception as e:
            LOG.error(e)
        LOG.error(f"Could not resolve a valid URL: {url}")

    def stop(self):
        if self.gui_enabled:
            self.gui.clear()
