# NEON AI (TM) SOFTWARE, Software Development Kit & Application Framework
# All trademark and other rights reserved by their respective owners
# Copyright 2008-2025 Neongecko.com Inc.
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

import pytest

from threading import Timer
from ovos_bus_client import Message
from neon_minerva.tests.skill_unit_test_base import SkillTestCase


def _node_message(program: str, action_supported: bool = True,
                  action_key: str = "launch_camera_app",
                  session_id: str = "node-test-1"):
    return Message("launch_program.intent", {"program": program}, {
        "node": {
            "node_id": "node-test-1",
            "node_name": "Test Node",
            "capabilities": {action_key: action_supported}
        },
        "session": {"session_id": session_id}
    })


def _response(action="launch_camera_app", status="success", error=None,
             session_id="node-test-1"):
    data = {"action": action, "status": status}
    if error:
        data["error"] = error
    return Message("node.invoke_native.response", data,
                   {"session": {"session_id": session_id}})


def _arm_node_reply(bus, response_message):
    """
    `FakeBus.emit` runs handlers synchronously, so replying to
    `node.invoke_native` from inside its own handler would emit the
    response before the helper's `wait_for_message` has subscribed. Reply
    from a short delay instead, after the handler's call stack unwinds.
    """
    def _reply(_m):
        Timer(0.05, lambda: bus.emit(response_message)).start()
    bus.once("node.invoke_native", _reply)


class TestSkillMethods(SkillTestCase):
    def test_00_skill_init(self):
        # Test any parameters expected to be set in init or initialize methods
        from neon_utils.skills import NeonSkill
        self.assertIsInstance(self.skill, NeonSkill)

    def test_launch_program_intent(self):
        # TODO
        pass

    def test_launch_node_program_supported_emits_invoke_native(self):
        message = _node_message("camera")
        emitted = []
        self.skill.bus.once("node.invoke_native",
                            lambda m: emitted.append(m))
        _arm_node_reply(self.skill.bus, _response(status="success"))

        self.skill.handle_launch_program(message)

        self.assertEqual(len(emitted), 1)
        self.assertEqual(emitted[0].data["action"], "launch_camera_app")
        self.assertEqual(emitted[0].data["params"], {})

    def test_launch_node_program_unsupported_capability(self):
        # skill-launcher ships native_action_*.dialog files, so the
        # neon-utils helper prefers speak_dialog over its plain-text fallback.
        message = _node_message("camera", action_supported=False)

        self.skill.handle_launch_program(message)

        self.skill.speak.assert_not_called()
        self.skill.speak_dialog.assert_called_once_with(
            "native_action_not_supported",
            {"action": "launch_camera_app",
             "description": "the camera app"},
            message=message)

    def test_launch_node_program_unmapped_program_not_supported(self):
        message = _node_message("some unknown program")

        self.skill.handle_launch_program(message)

        self.skill.speak_dialog.assert_called_once_with(
            "not_supported", private=True)

    def test_launch_node_program_maps_alarm_to_clock_action(self):
        message = _node_message("alarm", action_key="launch_clock_app")
        emitted = []
        self.skill.bus.once("node.invoke_native",
                            lambda m: emitted.append(m))
        _arm_node_reply(self.skill.bus,
                       _response(action="launch_clock_app", status="success"))

        self.skill.handle_launch_program(message)

        self.assertEqual(emitted[0].data["action"], "launch_clock_app")
        self.skill.speak.assert_not_called()  # confirm_on_success defaults off
        self.skill.speak_dialog.assert_not_called()

    def test_launch_node_program_maps_messages_to_sms_bare_launch(self):
        message = _node_message("messages", action_key="launch_sms_app")
        emitted = []
        self.skill.bus.once("node.invoke_native",
                            lambda m: emitted.append(m))
        _arm_node_reply(self.skill.bus,
                       _response(action="launch_sms_app", status="success"))

        self.skill.handle_launch_program(message)

        self.assertEqual(emitted[0].data["action"], "launch_sms_app")
        self.assertEqual(emitted[0].data["params"], {})
        self.skill.speak.assert_not_called()
        self.skill.speak_dialog.assert_not_called()

    def test_launch_node_program_full_mapping_table(self):
        from skill_launcher import PROGRAM_TO_NATIVE_ACTION

        for program, action in PROGRAM_TO_NATIVE_ACTION.items():
            with self.subTest(program=program):
                message = _node_message(program, action_key=action.value)
                emitted = []
                self.skill.bus.once("node.invoke_native",
                                    lambda m: emitted.append(m))
                _arm_node_reply(self.skill.bus,
                               _response(action=action.value,
                                        status="success"))

                self.skill.handle_launch_program(message)

                self.assertEqual(emitted[0].data["action"], action.value)

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
