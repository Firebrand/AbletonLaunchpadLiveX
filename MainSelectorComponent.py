from __future__ import absolute_import, print_function, unicode_literals
from _Framework.SessionZoomingComponent import DeprecatedSessionZoomingComponent
from .SpecialSessionComponent import SpecialSessionComponent
from .SubSelectorComponent import *
from .Log import log
import time

SESSION_MODE = 0
USER_1_MODE = 1
USER_2_MODE = 2
MIXER_MODE = 3

class MainSelectorComponent(ModeSelectorComponent):
    u""" Class that reassigns the button on the launchpad to different functions """

    def __init__(self, matrix, top_buttons, side_buttons, config_button):
        assert isinstance(matrix, ButtonMatrixElement)
        assert matrix.width() == 8 and matrix.height() == 8
        assert isinstance(top_buttons, tuple)
        assert len(top_buttons) == 8
        assert isinstance(side_buttons, tuple)
        assert len(side_buttons) == 8
        assert isinstance(config_button, ButtonElement)
        ModeSelectorComponent.__init__(self)
        self._session = SpecialSessionComponent(matrix.width(), matrix.height())
        self._zooming = DeprecatedSessionZoomingComponent(self._session)
        self._session.name = 'Session_Control'
        self._zooming.name = 'Session_Overview'
        self._matrix = matrix
        self._side_buttons = side_buttons
        self._nav_buttons = top_buttons[:4]
        self._config_button = config_button
        self._zooming.set_empty_value(LED_OFF)
        self._all_buttons = []
        for button in self._side_buttons + self._nav_buttons:
            self._all_buttons.append(button)

        self._update_stop_clips_led_callback = None  # keep the original callback for LED colors of stop buttons

        self._sub_modes = SubSelectorComponent(matrix, side_buttons, self._session)
        self._sub_modes.name = 'Mixer_Modes'
        self._sub_modes.set_update_callback(self._update_control_channels)
        self._init_session()
        self._all_buttons = tuple(self._all_buttons)
        self.set_modes_buttons(top_buttons[4:])
        self._long_press_delay = 0.5  # Long press delay in seconds
        self._button_press_times = {}
        self._delete_mode = False

    def disconnect(self):
        for button in self._modes_buttons:
            button.remove_value_listener(self._mode_value)

        self._session = None
        self._zooming = None
        for button in self._all_buttons:
            button.set_on_off_values(127, LED_OFF)

        self._config_button.turn_off()
        self._matrix = None
        self._side_buttons = None
        self._nav_buttons = None
        self._config_button = None
        ModeSelectorComponent.disconnect(self)
        return

    def session_component(self):
        return self._session

    def set_modes_buttons(self, buttons):
        assert buttons == None or isinstance(buttons, tuple) or len(buttons) == self.number_of_modes()
        identify_sender = True
        for button in self._modes_buttons:
            button.remove_value_listener(self._mode_value)

        self._modes_buttons = []
        if buttons != None:
            for button in buttons:
                assert isinstance(button, ButtonElement)
                self._modes_buttons.append(button)
                button.add_value_listener(self._mode_value, identify_sender)

        self.set_mode(SESSION_MODE)
        return

    def number_of_modes(self):
        return 4

    def on_enabled_changed(self):
        self.update()

    def set_mode(self, mode):
        assert mode in range(self.number_of_modes())
        if self._mode_index != mode or mode == MIXER_MODE:
            self._mode_index = mode
            if mode == USER_1_MODE:
                # Set the mode to MIXER_MODE when USER_1_MODE is selected
                self._mode_index = MIXER_MODE
                # Set the sub-mode to volume control (assuming 0 is the volume sub-mode)
                self._sub_modes.set_mode(0)
            self.update()

    def channel_for_current_mode(self):
        new_channel = self._mode_index + self._sub_modes.mode()
        if new_channel > 0:
            new_channel += 3
        return new_channel

    def update(self):
        super(MainSelectorComponent, self).update()
        assert self._modes_buttons != None
        if self.is_enabled():
            for index in range(len(self._modes_buttons)):
                self._modes_buttons[index].set_force_next_value()
                if index == self._mode_index:
                    self._modes_buttons[index].turn_on()
                else:
                    self._modes_buttons[index].turn_off()

            for scene_index in range(8):
                self._side_buttons[scene_index].set_enabled(True)
                for track_index in range(8):
                    self._matrix.get_button(track_index, scene_index).set_enabled(True)

            for button in self._nav_buttons:
                button.set_enabled(True)

            as_active = True
            as_enabled = True
            self._session.set_allow_update(False)
            self._zooming.set_allow_update(False)
            self._config_button.send_value(40)
            self._config_button.send_value(1)
            release_buttons = self._mode_index == USER_1_MODE
            if self._mode_index == SESSION_MODE:
                self._setup_mixer(not as_active)
                self._setup_session(as_active, as_enabled)
            elif self._mode_index == USER_1_MODE:
                # This case shouldn't be reached now, but keep it for consistency
                self._setup_session(not as_active, not as_enabled)
                self._setup_mixer(as_active)
                self._sub_modes.set_mode(0)  # Set to volume control
            elif self._mode_index == USER_2_MODE:
                self._setup_session(not as_active, not as_enabled)
                self._setup_mixer(not as_active)
                self._setup_user(release_buttons)
            elif self._mode_index == MIXER_MODE:
                self._setup_session(not as_active, as_enabled)
                self._setup_mixer(as_active)
            else:
                assert False
            self._session.set_allow_update(True)
            self._zooming.set_allow_update(True)
            self._update_control_channels()
        return

    def _update_control_channels(self):
        new_channel = self.channel_for_current_mode()
        for button in self._all_buttons:
            button.set_channel(new_channel)
            button.set_force_next_value()

    def _delete_clip_button(self, value):
        self._delete_mode = True

    def _set_active_track(self, track_index):
        if track_index < len(self.song().tracks):
            self.song().view.selected_track = self.song().tracks[track_index]

    def _do_nothing(self, param1):
        return

    def _setup_session(self, as_active, as_enabled):
        assert isinstance(as_active, type(False))

        if self._update_stop_clips_led_callback is None:  # first time
            self._update_stop_clips_led_callback = self._session._update_stop_clips_led
        if as_active:
            self._session._update_stop_clips_led = self._do_nothing  # in session mode, the last row "stop buttons" shouldn't display colors
        else:
            self._session._update_stop_clips_led = self._update_stop_clips_led_callback  # normal behaviour for stop buttons in mixer mode            

        for button in self._nav_buttons:
            if as_enabled:
                button.set_on_off_values(GREEN_FULL, GREEN_THIRD)
            else:
                button.set_on_off_values(127, LED_OFF)

        for scene_index in range(8):
            scene = self._session.scene(scene_index)
            if as_active:
                scene_button = self._side_buttons[scene_index]
                scene_button.set_on_off_values(127, LED_OFF)
                if scene_index == 7:  # delete clip
                    scene_button.set_on_off_values(RED_FULL, RED_FULL)
                    scene_button.turn_on() 
                    scene_button.add_value_listener(self._delete_clip_button)
                else:
                    scene.set_launch_button(None)
                    scene_button.add_value_listener(self._on_scene_button_pressed, identify_sender=True)
            else:
                scene.set_launch_button(None)
            for track_index in range(8):
                if as_active:
                    button = self._matrix.get_button(track_index, scene_index)
                    button.add_value_listener(self._on_matrix_button_pressed, identify_sender=True)
                    if scene_index == 7:  
                        button.turn_off()
                    else:
                        button.set_on_off_values(127, LED_OFF)
                        scene.clip_slot(track_index).set_launch_button(button)
                else:
                    scene.clip_slot(track_index).set_launch_button(None)

            self._session.set_stop_track_clip_buttons(tuple([self._matrix.get_button(t, 7) for t in range(8)]))  # last row = stop buttons in session mode

        if as_active:
            self._zooming.set_zoom_button(self._modes_buttons[0])
            self._zooming.set_button_matrix(self._matrix)
            self._zooming.set_scene_bank_buttons(self._side_buttons)
            self._zooming.set_nav_buttons(self._nav_buttons[0], self._nav_buttons[1], self._nav_buttons[2], self._nav_buttons[3])
            self._zooming.update()
        else:
            self._zooming.set_zoom_button(None)
            self._zooming.set_button_matrix(None)
            self._zooming.set_scene_bank_buttons(None)
            self._zooming.set_nav_buttons(None, None, None, None)
            self._side_buttons[7].remove_value_listener(self._delete_clip_button)  # remove the delete clip button

        if as_enabled:
            self._session.set_track_bank_buttons(self._nav_buttons[3], self._nav_buttons[2])
            self._session.set_scene_bank_buttons(self._nav_buttons[1], self._nav_buttons[0])
        else:
            self._session.set_track_bank_buttons(None, None)
            self._session.set_scene_bank_buttons(None, None)
        return
    
    def _on_matrix_button_pressed(self, value, sender, *args):
        if value == 0:  # Button pressed
            for track_index in range(8):
                for scene_index in range(8):
                    if sender == self._matrix.get_button(track_index, scene_index):
                        self._set_active_track(track_index)
                        if self._delete_mode:
                            self._delete_clip(track_index, scene_index)
                            self._delete_mode = False
                        return

    def _delete_clip(self, track_index, scene_index):
        if track_index < len(self.song().tracks) and scene_index < len(self.song().scenes):
                track = self.song().tracks[track_index]
                if track and scene_index < len(track.clip_slots):
                    clip_slot = track.clip_slots[scene_index]
                    if clip_slot:
                        if clip_slot.has_clip:
                            clip_slot.delete_clip()
    
    def _on_scene_button_pressed(self, value, sender):   
        if self._mode_index == SESSION_MODE:
            
            scene_index = list(self._side_buttons).index(sender)
            if value != 0:  # Button pressed
                self._button_press_times[sender] = time.time()
            else:  # Button released
                press_time = self._button_press_times.get(sender, 0)
                if time.time() - press_time >= self._long_press_delay:
                    self._duplicate_row(sender)
                else:
                    self.song().scenes[scene_index].fire()
                del self._button_press_times[sender]

            self._session.set_stop_track_clip_buttons(tuple([self._matrix.get_button(t, 7) for t in range(8)]))  # last row = stop buttons in session mode



    def _duplicate_row(self, button):
        for i, scene_button in enumerate(self._side_buttons):
            if scene_button == button:
                source_scene_index = i
                target_scene_index = i + 1
                break
        else:
            return  # Button not found

        if target_scene_index >= 8:
            return  # Can't duplicate the last row

        source_scene = self._session.scene(source_scene_index)
        target_scene = self._session.scene(target_scene_index)

        for track_index in range(8):
            source_clip_slot = source_scene.clip_slot(track_index)._clip_slot
            target_clip_slot = target_scene.clip_slot(track_index)._clip_slot

            if source_clip_slot.has_clip:
                if target_clip_slot.has_clip:
                    target_clip_slot.delete_clip()
                source_clip_slot.duplicate_clip_to(target_clip_slot)

    def _setup_mixer(self, as_active):
        assert isinstance(as_active, type(False))
        if as_active and self._sub_modes.is_enabled():
            self._sub_modes.set_mode(-1)
        self._sub_modes.set_enabled(as_active)

    def _setup_user(self, release_buttons):
        for scene_index in range(8):
            scene_button = self._side_buttons[scene_index]
            scene_button.set_on_off_values(127, LED_OFF)
            scene_button.turn_off()
            scene_button.set_enabled(not release_buttons)
            for track_index in range(8):
                button = self._matrix.get_button(track_index, scene_index)
                button.set_on_off_values(127, LED_OFF)
                button.turn_off()
                button.set_enabled(not release_buttons)

        for button in self._nav_buttons:
            button.set_on_off_values(127, LED_OFF)
            button.turn_off()
            button.set_enabled(not release_buttons)

        if self._mode_index == USER_1_MODE:
            self._config_button.send_value(2)
        self._config_button.send_value(32, force=True)

    def _init_session(self):
        self._session.set_stop_clip_value(AMBER_THIRD)
        self._session.set_stop_clip_triggered_value(AMBER_BLINK)
        for scene_index in range(self._matrix.height()):
            scene = self._session.scene(scene_index)
            scene.set_triggered_value(GREEN_BLINK)
            scene.name = 'Scene_' + str(scene_index)
            for track_index in range(self._matrix.width()):
                clip_slot = scene.clip_slot(track_index)
                clip_slot.set_triggered_to_play_value(GREEN_BLINK)
                clip_slot.set_triggered_to_record_value(RED_BLINK)
                clip_slot.set_stopped_value(AMBER_FULL)
                clip_slot.set_started_value(GREEN_FULL)
                clip_slot.set_recording_value(RED_FULL)
                clip_slot.name = str(track_index) + '_Clip_Slot_' + str(scene_index)
                self._all_buttons.append(self._matrix.get_button(track_index, scene_index))

        self._zooming.set_stopped_value(RED_FULL)
        self._zooming.set_selected_value(AMBER_FULL)
        self._zooming.set_playing_value(GREEN_FULL)
