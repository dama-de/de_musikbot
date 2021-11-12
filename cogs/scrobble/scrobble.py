import logging
from datetime import datetime, timedelta

from discord import Member, Spotify
from discord.ext.commands import Cog

from cogs.music.classes import Track

log = logging.getLogger(__name__)


class Scrobble(Cog):

    @Cog.listener()
    async def on_member_update(self, before: Member, after: Member):
        now = datetime.utcnow()

        # See if there actually was an activity change and not something else
        if before.activity is not after.activity:
            # Track was paused OR last track finished
            if isinstance(before.activity, Spotify) and not after.activity:
                track = self.pack_spotify_activity(before.activity)
                log.info(f"Pause: {track.artist.name} - {track.name}")

            # Resumed, or started a new playlist
            elif not before.activity and isinstance(after.activity, Spotify):
                track = self.pack_spotify_activity(after.activity)
                log.info(f"Play: {track.artist.name} - {track.name}")

            # Scrub or track change
            elif isinstance(before.activity, Spotify) and isinstance(after.activity, Spotify):
                before_track = self.pack_spotify_activity(before.activity)
                after_track = self.pack_spotify_activity(after.activity)

                # Scrubbed through current track. Current time must be before predicted end of the previous track.
                if before_track == after_track and now < before.activity.end:
                    log.info(f"Scrubbed: {after_track.artist.name} - {after_track.name}")

                # Track changed within playlist
                else:
                    log.info(f"Track change:  {after_track.artist.name} - {after_track.name}")

                    created_before_start = before.activity.created_at <= before.activity.start + timedelta(seconds=1)
                    now_after_end = now + timedelta(seconds=1) >= before.activity.end

                    log.info(f"created: {before.activity.created_at}")
                    log.info(f"start:   {before.activity.start}")
                    log.info(f"end:     {before.activity.end}")
                    log.info(f"now:     {now}")

                    # Track was started from the beginning and played until the predicted end (no scrubbing)
                    if created_before_start and now_after_end:
                        log.info(f"Played through.")

    def pack_spotify_activity(self, activity: Spotify) -> Track:
        result = Track()
        result.name = activity.title
        result.artist.name = activity.artist
        result.album.name = activity.album
        return result
