# -*- coding: utf-8 -*-
"""
    Copyright (C) 2017 Sebastian Golasch (plugin.video.netflix)
    Copyright (C) 2019 Stefano Gottardo - @CastagnaIT (original implementation module)
    Manages events to send to the netflix service for the progress of the played video

    SPDX-License-Identifier: MIT
    See LICENSES/MIT.md for more information.
"""
from __future__ import absolute_import, division, unicode_literals

import resources.lib.common as common
from resources.lib.common.cache_utils import CACHE_BOOKMARKS, CACHE_COMMON, CACHE_MANIFESTS
from resources.lib.common.exceptions import InvalidVideoListTypeError
from resources.lib.globals import G
from resources.lib.services.msl.msl_utils import EVENT_START, EVENT_ENGAGE, EVENT_STOP, EVENT_KEEP_ALIVE
from resources.lib.utils.esn import get_esn
from resources.lib.utils.logging import LOG
from .action_manager import ActionManager


class AMVideoEvents(ActionManager):
    """Detect the progress of the played video and send the data to the netflix service"""

    SETTING_ID = 'ProgressManager_enabled'

    def __init__(self):
        super(AMVideoEvents, self).__init__()
        self.event_data = {}
        self.is_event_start_sent = False
        self.last_tick_count = 0
        self.tick_elapsed = 0
        self.is_player_in_pause = False
        self.lock_events = False
        self.allow_request_update_loco = False

    def __str__(self):
        return 'enabled={}'.format(self.enabled)

    def initialize(self, data):
        if not data['event_data']:
            LOG.warn('AMVideoEvents: disabled due to no event data')
            self.enabled = False
            return
        self.event_data = data['event_data']

    def on_playback_started(self, player_state):
        self.event_data['manifest'] = _get_manifest(self.videoid)
        # Clear continue watching list data on the cache, to force loading of new data
        # but only when the videoid not exists in the continue watching list
        try:
            videoid_exists, list_id = common.make_http_call('get_continuewatching_videoid_exists',
                                                            {'video_id': str(self.videoid_parent.value)})
            if not videoid_exists:
                # Delete the cache of continueWatching list
                G.CACHE.delete(CACHE_COMMON, list_id, including_suffixes=True)
                # When the continueWatching context is invalidated from a refreshListByContext call
                # the LoCo need to be updated to obtain the new list id, so we delete the cache to get new data
                G.CACHE.delete(CACHE_COMMON, 'loco_list')
        except InvalidVideoListTypeError:
            # Ignore possible "No lists with context xxx available" exception due to a new profile without data
            pass

    def on_tick(self, player_state):
        if self.lock_events:
            return
        if self.is_player_in_pause and (self.tick_elapsed - self.last_tick_count) >= 1800:
            # When the player is paused for more than 30 minutes we interrupt the sending of events (1800secs=30m)
            self._send_event(EVENT_ENGAGE, self.event_data, player_state)
            self._send_event(EVENT_STOP, self.event_data, player_state)
            self.is_event_start_sent = False
            self.lock_events = True
        else:
            if not self.is_event_start_sent:
                # We do not use _on_playback_started() to send EVENT_START, because the action managers
                # AMStreamContinuity and AMPlayback may cause inconsistencies with the content of player_state data

                # When the playback starts for the first time, for correctness should send elapsed_seconds value to 1
                if self.tick_elapsed < 5 and self.event_data['resume_position'] is None:
                    player_state['elapsed_seconds'] = 1
                self._send_event(EVENT_START, self.event_data, player_state)
                self.is_event_start_sent = True
                self.tick_elapsed = 0
            else:
                # Generate events to send to Netflix service every 1 minute (60secs=1m)
                if (self.tick_elapsed - self.last_tick_count) >= 60:
                    self._send_event(EVENT_KEEP_ALIVE, self.event_data, player_state)
                    self._save_resume_time(player_state['elapsed_seconds'])
                    self.last_tick_count = self.tick_elapsed
                    # Allow request of loco update (for continueWatching and bookmark) only after the first minute
                    # it seems that most of the time if sent earlier returns error
                    self.allow_request_update_loco = True
        self.tick_elapsed += 1  # One tick almost always represents one second

    def on_playback_pause(self, player_state):
        if not self.is_event_start_sent:
            return
        self._reset_tick_count()
        self.is_player_in_pause = True
        self._send_event(EVENT_ENGAGE, self.event_data, player_state)
        self._save_resume_time(player_state['elapsed_seconds'])

    def on_playback_resume(self, player_state):
        self.is_player_in_pause = False
        self.lock_events = False

    def on_playback_seek(self, player_state):
        if not self.is_event_start_sent or self.lock_events:
            # This might happen when the action manager AMPlayback perform a video skip
            return
        self._reset_tick_count()
        self._send_event(EVENT_ENGAGE, self.event_data, player_state)
        self._save_resume_time(player_state['elapsed_seconds'])
        self.allow_request_update_loco = True

    def on_playback_stopped(self, player_state):
        if not self.is_event_start_sent or self.lock_events:
            return
        self._reset_tick_count()
        self._send_event(EVENT_ENGAGE, self.event_data, player_state)
        self._send_event(EVENT_STOP, self.event_data, player_state)
        # Update the resume here may not always work due to race conditions with refresh list/stop event
        self._save_resume_time(player_state['elapsed_seconds'])

    def _save_resume_time(self, resume_time):
        """Save resume time value in order to update the infolabel cache"""
        # Why this, the video lists are requests to the web service only once and then will be cached in order to
        # quickly get the data and speed up a lot the GUI response.
        # Watched status of a (video) list item is based on resume time, and the resume time is saved in the cache data.
        # To avoid slowing down the GUI by invalidating the cache to get new data from website service, one solution is
        # save the values in memory and override the bookmark value of the infolabel.
        # The callback _on_playback_stopped can not be used, because the loading of frontend happen before.
        G.CACHE.add(CACHE_BOOKMARKS, self.videoid.value, resume_time)

    def _reset_tick_count(self):
        self.tick_elapsed = 0
        self.last_tick_count = 0

    def _send_event(self, event_type, event_data, player_state):
        if not player_state:
            LOG.warn('AMVideoEvents: the event [{}] cannot be sent, missing player_state data', event_type)
            return
        event_data['allow_request_update_loco'] = self.allow_request_update_loco
        common.send_signal(common.Signals.QUEUE_VIDEO_EVENT, {
            'event_type': event_type,
            'event_data': event_data,
            'player_state': player_state
        }, non_blocking=True)


def _get_manifest(videoid):
    """Get the manifest from cache"""
    cache_identifier = get_esn() + '_' + videoid.value
    return G.CACHE.get(CACHE_MANIFESTS, cache_identifier)
