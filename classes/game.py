import json
from datetime import datetime, date
from dataclasses import dataclass, field
from typing import ClassVar, Dict, List


class DataLoader:
        """Loads data stored in JSON files in assets folder.""" 
        @classmethod     
        def load(cls):
            try:
                with open("assets/words.json") as f:
                    Word._all_words = [w.upper() for w in json.load(f)]

                with open("assets/letter_values.json") as f:
                    Word._letter_values = json.load(f)

                with open("assets/itwords.json") as f:
                    ItWord._all_itwords = [w.upper() for w in json.load(f)]

                with open("assets/itword_archive.json") as f:
                    ItWord._archive = {date.fromisoformat(d): w for d, w in json.load(f).items()}

                with open("assets/rules.json") as f:
                    rules = json.load(f)
                    return rules

            except FileNotFoundError as e:
                raise FileNotFoundError("No such file or directory")

 
@dataclass(frozen=True)
class Word:
    """Loads a list of all valid words of 3-8 letters plus a dict of all letters and their corresponding points value"""
    word: str
  
    _all_words: ClassVar[List[str]] = []
    _letter_values: ClassVar[Dict[str, int]] = {}

    def value(self) -> int:
        """Calculate the value of a word using letter_values."""
        return sum(Word._letter_values[letter] for letter in self.word)


@dataclass(frozen=True)
class ItWord:
    """Loads a list of all valid ItWords."""
    _all_itwords: ClassVar[List[str]] = []


@dataclass
class DailyItWord:
    """Loads a list of all valid ItWords."""
    _itword: ItWord
    _archive: ClassVar[Dict[date, str]] = {}

    DAY_ZERO: ClassVar[date] = date(2026, 9, 1)  # Starting date for all_itwords cycling

    @classmethod
    def save_to_archive(cls):
        """Saves itword_archive to JSON file."""
        with open("assets/itword_archive.json", "w") as file:
            json.dump({d.isoformat(): w for d, w in cls._archive.items()}, file, indent=4)

    @classmethod
    def get_itword(cls, date: date) -> str:
        """Returns the ItWord for a given date, saves it to itword_archive if not already present."""
        if date in cls._archive:
            return cls._archive[date]
        
        _index = (date - cls.DAY_ZERO).days % len(ItWord._all_itwords) #this ensures all_itwords is continually cycled through        
        _itword = ItWord._all_itwords[_index]        
        cls._archive[date] = _itword 
        cls.save_to_archive() #saves updated itword_archive to JSON file

        return _itword  


@dataclass
class GameSession:
    """Tracks session analytics and returns length of session when it ends"""
    user: int
    start_time: datetime = field(default_factory=datetime.now)
    end_time: datetime | None = None
    word_length: int = 3
    first_letter_index: int = 0
    last_letter_index: int = 1
    game_round: int = 1
    max_rounds: int = 6
    total_guesses: int = 0
    total_score: int = 0
    valid_guessed_words: Dict[str, int] = field(default_factory=dict)

    def apply_valid_guess(self, guess, word_value: int):
        self.total_score += word_value
        self.valid_guessed_words[guess] = word_value
        self.word_length += 1
        self.game_round += 1
        self.first_letter_index += 1
        if self.game_round < self.max_rounds:
            self.last_letter_index += 1

    def apply_invalid_guess(self):
        self.total_score -= 1 #subtract 1 point for each invalid guess
 
    def finalize_session(self):
        if not self.end_time:
            return None
        
        _session_length = int((self.end_time - self.start_time).total_seconds())
        _minutes = _session_length // 60
        _seconds = _session_length % 60
        
        self.total_score -= _minutes  # Subtract 1 point for each minute taken to complete the game

        return _minutes, _seconds #only returns minutes and seconds to print to screen in Game.run method


@dataclass
class Guess:
    """Ensures user input meets game criteria and returns boolean"""
    gamesession: GameSession
    itword: str
    guess: str
    
    def __post_init__(self):
        self.guess = self.guess.upper() 
        self.gamesession.total_guesses += 1

        if self.valid:
            word_value = Word(self.guess).value()
            self.gamesession.apply_valid_guess(self.guess, word_value)    

        else:
          self.gamesession.apply_invalid_guess()         

    @property
    def first_letter_index(self) -> int:
        return self.gamesession.first_letter_index

    @property
    def last_letter_index(self) -> int:      
        return self.gamesession.last_letter_index

    @property
    def game_round(self) -> int:
        return self.gamesession.game_round
     
    @property
    def valid(self) -> bool:
        guess = self.guess

        return (
            guess in Word._all_words
            and len(guess) == self.gamesession.word_length
            and guess[0] == self.itword[self.first_letter_index]
            and (self.gamesession.game_round >= self.gamesession.max_rounds or guess[-1] == self.itword[self.last_letter_index])
    )   


class Game:
    def __init__(self):
        self.date = date.today()

    def get_user_guess(self):
        """Returns a correctly formatted word to print to screen for user to input guess."""
        _dash_string = " _ " * (self.game_session.game_round) 

        if self.game_session.game_round < self.game_session.max_rounds:
            _guess = f"{self.itword[self.game_session.first_letter_index]}{_dash_string}{self.itword[self.game_session.last_letter_index]}: "

        else:
            _guess = f"{self.itword[self.game_session.first_letter_index]}{_dash_string} _: "

        return input(_guess)    
         
    def run(self):
        """Run from main.py"""
        DataLoader.load()        
        user_ID = 12345 
        self.game_session = GameSession(user_ID)  
        self.itword = DailyItWord.get_itword(self.date)

        while self.game_session.game_round <= self.game_session.max_rounds:
            Guess(self.game_session, self.itword, self.get_user_guess())  

        self.game_session.end_time = datetime.now()  
        minutes, seconds = self.game_session.finalize_session()  #session duration details only required to print to screen

        print(f"You correctly entered: {self.game_session.valid_guessed_words}")    
        print(f"Number of guesses in total: {self.game_session.total_guesses}")  
        print(f"Time to complete: {minutes} min {seconds} sec") 
        print(f"Total score: {self.game_session.total_score} points")
    

