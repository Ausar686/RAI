# Created by: Ausar686
# https://github.com/Ausar686

import os
from collections import defaultdict

import numpy as np

from ..storages import Actions, Diary, MediaStorage, UserData 


class Profile: 
    _user_data_filename = "user.json"
    _diary_filename = "diary.csv"
    _actions_filename = "actions.csv"
    _media_data_filename = "media.csv"
    
    def __init__(
        self,
        load_dir: str=None,
        *,
        user_data: UserData=None,
        diary: Diary=None,
        actions: Actions=None,
        media: MediaStorage=None,
        default_dir: str=None):
        if load_dir is not None:
            self.load(load_dir)
            return
        if isinstance(user_data, UserData):
            self.user_data = user_data
        else:
            self.user_data = UserData()
        if isinstance(diary, Diary):
            self.diary = diary
        else:
            self.diary = Diary()
        if isinstance(actions, Actions):
            self.actions = actions
        else:
            self.actions = Actions()
        if isinstance(media, MediaStorage):
            self.media = media
        else:
            self.media = MediaStorage()
        if default_dir is None:
            self.default_dir = load_dir
        else:
            self.default_dir = default_dir
        self.up_to_date = True
        return
    
    def get_emotions_data(self, value: str=None) -> dict:
        df = self.diary.get(by="emotion", value=value)
        if df.empty:
            return {}
        values = df["reason"].value_counts()
        emotions_data = {key: values[key] for key in values}
        return emotions_data
    
    def get_media_data(self, media: str=None) -> dict:
        df = self.actions.get(by="media", value=media)
        if df.empty:
            return {}
        values = df[["title", "author"]].value_counts()
        media_data = dict(values)
        return media_data
    
    def add_emotion(self, emotion: dict) -> None:
        self.diary.append(emotion)
        self.up_to_date = False
        return
    
    def add_action(self, action: dict) -> None:
        self.actions.append(action)
        self.up_to_date = False
        return
    
    @staticmethod
    def _score_function(array: np.array) -> np.array:
        return np.exp(0.25*(array-array.shape[0]))
    
    def _update_actions_data(self) -> None:
        self.actions.data["score"] = self._score_function(self.actions.data.index)
        self.actions.data["_topic"] = self.actions.data.topic.str.split("|").fillna(self.actions.data.topic)
        self.actions.data = self.actions.data.explode("_topic") # Check this
        self.user_data._fav_actions_topics = defaultdict(float, [(topic, df.score.sum()) 
                                                        for topic, df in self.actions.data.groupby(by="_topic")])
        return
        
    def _update_diary_data(self) -> None:
        self.diary.data["score"] = self._score_function(self.diary.data.index)
        self.diary.data["_emotion"] = self.diary.data.emotion.str.split("|").fillna(self.diary.data.emotion)
        self.diary.data = self.diary.data.explode("_emotion") # Check this
        self.user_data._fav_diary_topics = defaultdict(float, [(topic, df.score.sum()) 
                                                     for topic, df in self.diary.data.groupby(by="_emotion")])
        return
        
    def _update_fav_topics(self) -> None:
        topics = set(self.user_data._fav_diary_topics.keys()) | set(self.user_data._fav_actions_topics.keys())
        self.user_data._fav_topics = \
            defaultdict(float, [(topic, self.user_data._fav_diary_topics[topic] + self.user_data._fav_actions_topics[topic]) 
                                for topic in topics])
        return
    
    def _update_media_data(self) -> None:
        self.media.data["_topic"] = self.media.data.topic.str.split("|").fillna(self.media.data.topic)
        self.media.data = self.media.data.explode("_topic") # Check this
        self.media.data["score"] = self.media.data["_topic"].map(self.user_data._fav_topics)
        summarized_df = self.media.data.groupby(level=0)["score"].sum()
        self.media.data.drop(["_topic", "score"], axis=1, inplace=True)
        self.media.data.drop_duplicates(inplace=True)
        self.media.data["score"] = summarized_df
        return
    
    def update(self) -> None:
        if self.up_to_date:
            return
        # Update actions' scores
        self._update_actions_data()
        # Update diary scores
        self._update_diary_data()
        # Update favourite topics in user_data._fav_topics defaultdict.
        self._update_fav_topics()
        # Update media relevance scores
        self._update_media_data()
        # Set the flag so that not to update data before actual action or diary note.
        self.up_to_date = True
        return
    
    def load(self, load_dir: str=None) -> None:
        if load_dir is None:
            raise ValueError("Can't load from None directory.")
        # Set paths to files with data
        user_data_path = os.path.join(load_dir, self._user_data_filename)
        diary_path = os.path.join(load_dir, self._diary_filename)
        actions_path = os.path.join(load_dir, self._actions_filename)
        media_data_path = os.path.join(load_dir, self._media_data_filename)
        # Create UserData from JSON
        self.user_data = UserData(user_data_path)
        # Create Diary from path
        self.diary = Diary(diary_path)
        # Create Actions from path
        self.actions = Actions(actions_path)
        # Create MediaStorage from path
        self.media = MediaStorage(media_data_path)
        # Set default directory for further 'to_disk' and 'load' usage
        self.default_dir = load_dir
        # Set 'up_to_date' attribute for updating
        self.up_to_date = False
        # Update the data in profile
        self.update()
        return
    
    def to_disk(self, output_dir: str=None) -> None:
        if output_dir is None:
            output_dir = self.default_dir
        if not os.path.exists(output_dir):
            raise ValueError("Output directory does not exist.")
        # Set paths to files with data
        user_data_path = os.path.join(output_dir, self._user_data_filename)
        diary_path = os.path.join(output_dir, self._diary_filename)
        actions_path = os.path.join(output_dir, self._actions_filename)
        media_data_path = os.path.join(output_dir, self._media_data_filename)
        # Write data to disk
        self.user_data.to_disk(user_data_path)
        self.diary.to_disk(diary_path)
        self.actions.to_disk(actions_path)
        self.media.to_disk(media_data_path)
        return