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
import os.path
import shutil
import unittest
import pytest
import json

from os import mkdir
from os.path import dirname, join, exists
from mock import Mock
from mycroft_bus_client import Message
from ovos_utils.messagebus import FakeBus

from mycroft.skills.skill_loader import SkillLoader


class TestSkillMethods(unittest.TestCase):

    @classmethod
    def setUpClass(cls) -> None:
        bus = FakeBus()
        bus.run_in_thread()
        skill_loader = SkillLoader(bus, dirname(dirname(__file__)))
        skill_loader.load()
        cls.skill = skill_loader.instance

        # Define a directory to use for testing
        cls.test_fs = join(dirname(__file__), "skill_fs")
        if not exists(cls.test_fs):
            mkdir(cls.test_fs)

        # Override the fs paths to use the test directory
        cls.skill.settings_write_path = cls.test_fs
        cls.skill.file_system.path = cls.test_fs

        # Override speak and speak_dialog to test passed arguments
        cls.skill.speak = Mock()
        cls.skill.speak_dialog = Mock()

    def setUp(self):
        self.skill.speak.reset_mock()
        self.skill.speak_dialog.reset_mock()

    def tearDown(self) -> None:
        self.skill.bus.remove_all_listeners("neon.wake_words_state")

    @classmethod
    def tearDownClass(cls) -> None:
        shutil.rmtree(cls.test_fs)

    def test_00_skill_init(self):
        # Test any parameters expected to be set in init or initialize methods
        from neon_utils.skills import NeonSkill
        self.assertIsInstance(self.skill, NeonSkill)

    def test_launch_program_intent(self):
        # TODO
        pass

    def test_browse_website_intent(self):
        # TODO
        pass

    def test_parse_page_in_request(self):
        no_page = "google dot com"
        with_page = "images on google dot com"
        self.assertEqual(self.skill._parse_page_in_request(no_page),
                         (None, no_page))
        self.assertEqual(self.skill._parse_page_in_request(with_page),
                         ("images", "google dot com"))

    def test_parse_url_from_website(self):
        valid_url = "google.com"
        transcribed_dot = "git hub dot com"
        no_tld = "klat"
        neon_special_case = "neon"
        with_domain_word = "yahoo com"
        multi_word_no_tld = "neon gecko"
        no_tld_with_dot = "duck duck go."

        self.assertEqual(self.skill._parse_url_from_website(valid_url),
                         valid_url)
        self.assertEqual(self.skill._parse_url_from_website(transcribed_dot),
                         "github.com")
        self.assertEqual(self.skill._parse_url_from_website(no_tld),
                         "klat.com")
        self.assertEqual(self.skill._parse_url_from_website(neon_special_case),
                         "neon.ai")
        self.assertEqual(self.skill._parse_url_from_website(with_domain_word),
                         "yahoo.com")
        self.assertEqual(self.skill._parse_url_from_website(multi_word_no_tld),
                         "neongecko.com")
        self.assertEqual(self.skill._parse_url_from_website(no_tld_with_dot),
                         "duckduckgo.com")

    def test_validate_url(self):
        valid_url = "https://neon.ai"
        http_url = "http://neon.ai"
        no_schema = "neon.ai"
        invalid_url = "neon ai"

        self.assertEqual(self.skill._validate_url(valid_url), valid_url)
        self.assertEqual(self.skill._validate_url(http_url), http_url)
        self.assertEqual(self.skill._validate_url(no_schema), valid_url)
        self.assertIsNone(self.skill._validate_url(invalid_url))


if __name__ == '__main__':
    pytest.main()
