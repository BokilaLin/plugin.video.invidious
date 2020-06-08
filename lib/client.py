# -*- coding: utf-8 -*-


from __future__ import absolute_import, division, unicode_literals


import collections

from six.moves.urllib.parse import urlunsplit, urlsplit

import objects
from iapc import Client


# ------------------------------------------------------------------------------
# Client
# ------------------------------------------------------------------------------

class InvidiousClient(object):

    _defaults_ = {
        "video": None,
        "playlists": {"playlists": [], "continuation": None},
        "playlist": {"videos": [], "title": None, "authorId": None, "playlistId": None}
    }

    _search_ = {
        "video": objects.Videos,
        "channel": objects.Channels,
        "playlist": objects.Playlists
    }

    def __init__(self):
        self.client = Client()
        self.queries = collections.deque()

    # --------------------------------------------------------------------------

    def query_(self, key, *args, **kwargs):
        return self.client.query(key, *args, **kwargs) or self._defaults_.get(key, [])

    def channel_(self, authorId):
        data = self.client.channel(authorId)
        if data:
            return objects.Channel(data)

    def instances_(self, **kwargs):
        return [instance[0] for instance in self.client.instances(**kwargs)
                if instance[1]["type"] in ("http", "https")]

    # --------------------------------------------------------------------------

    def video(self, **kwargs):
        video = self.query_("video", kwargs.pop("videoId"), **kwargs)
        if video:
            video = objects.Video(video)
            url, manifest, mime = (video.dashUrl, "mpd", "application/dash+xml")
            if video.liveNow:
                url, manifest, mime = (video.hlsUrl, "hls", None)
            split = urlsplit(url)
            url = urlunsplit((split.scheme or self.client.scheme(),
                              split.netloc or self.client.netloc(),
                              split.path, split.query, split.fragment))
            return (video._item(url), manifest, mime)

    # --------------------------------------------------------------------------

    def feed(self, ids, page=1, **kwargs):
        data, limit = self.client.feed(ids, page=page, **kwargs)
        return objects.Videos(data, limit=limit)

    def top(self, **kwargs):
        return objects.StdVideos(self.query_("top", **kwargs))

    def popular(self, **kwargs):
        return objects.ShortVideos(self.query_("popular", **kwargs))

    def trending(self, **kwargs):
        return objects.Videos(
            self.query_("trending", **kwargs), category=kwargs.get("type"))

    def playlists(self, **kwargs):
        category = None
        authorId = kwargs.pop("authorId")
        data = self.query_("playlists", authorId, **kwargs)
        channel = self.channel_(authorId)
        if channel:
            category = channel.author
            if channel.autoGenerated:
                data["continuation"] = None
        return objects.ChannelPlaylists(
            data["playlists"], continuation=data["continuation"],
            category=category)

    def channel(self, page=1, limit=60, **kwargs):
        category = None
        authorId = kwargs.pop("authorId")
        data = self.query_("videos", authorId, page=page, **kwargs)
        channel = self.channel_(authorId)
        if channel:
            category = channel.author
            if channel.autoGenerated:
                limit = 0
        return objects.Videos(data, limit=limit, category=category)

    def playlist(self, page=1, limit=100, **kwargs):
        data = self.query_(
            "playlist", kwargs.pop("playlistId"), page=page, **kwargs)
        authorId = data.get("authorId")
        if authorId:
            channel = self.channel_(authorId)
            if channel and channel.autoGenerated:
                limit = 0
        return objects.BaseVideos(
            data["videos"], category=data["title"], limit=limit)

    def search(self, q, page=1, limit=20, **kwargs):
        return self._search_[kwargs["type"]](
            self.query_("search", q=q, page=page, **kwargs), limit=limit)


client = InvidiousClient()

