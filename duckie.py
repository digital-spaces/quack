# DuckEngine (aka duckie) v2
# Copyright 2021 Morgan Fox, All Rights Reserved
import json
from os.path import exists
from os import remove
from tkinter import *
import tkinter.font as tkFont


class Window(Frame):
    def send_input(self, name):  # Name isn't used but tkinter throws a fit without it as an argument
        self.game.states[self.game.state]()

    def send_button_input(self):
        self.game.states[self.game.state]()

    def on_closing(self):
        self.game.running = False
        quit()

    def __init__(self, master, game):
        # Creation
        Frame.__init__(self, master)
        self.master = master
        self.master.tk_setPalette(background='#252525', foreground="#33ff33")
        self.master.wm_title("Quack")
        self.master.geometry("1024x468")
        self.master.resizable(0, 0)
        self.master.protocol("WM_DELETE_WINDOW", self.on_closing)

        self.game = game

        self.game_font = tkFont.Font(family="Courier")

        # Root grid
        self.master.columnconfigure(0)
        self.master.columnconfigure(1)
        self.master.rowconfigure(0, weight=2)
        self.master.rowconfigure(1, weight=1)

        # Display frame
        self.display_frame = Frame(self.master, width=100, height=100)
        self.display_frame.grid(column=0, row=0, sticky=NSEW, columnspan=1)

        # Status frame
        self.status_frame = Frame(self.master, width=100)
        self.status_frame.grid(column=1, row=0, sticky=NSEW)
        # Room
        self.status_room = Label(self.status_frame, justify=LEFT, width=33, anchor="w",
                                 font=self.game_font, text="")
        self.status_room.grid(column=0, row=0, sticky=W)
        # Map
        self.status_map = Label(self.status_frame, justify=LEFT, width=33, anchor="w",
                                font=self.game_font, text="")
        self.status_map.grid(column=0, row=1, sticky=W)
        # Inventory
        self.status_inventory = Label(self.status_frame, justify=LEFT, width=33, anchor="w",
                                      font=self.game_font, text="")
        self.status_inventory.grid(column=0, row=2, sticky=W)

        # Input frame
        self.input_frame = Frame(self.master)
        self.input_frame.grid(column=0, row=1, sticky=S, columnspan=2)
        # Prompt
        self.prompt = Entry(self.input_frame, font=self.game_font, width=100)
        self.prompt.bind('<Return>', self.send_input)
        self.prompt.grid(column=0, row=1, sticky=S)
        # Button
        self.button = Button(self.input_frame, text="Send", font=self.game_font, command=self.send_button_input)
        self.button.grid(column=0, row=1, sticky=EW, columnspan=2)


class Game:
    def __init__(self, game_data):
        self.window = Window(Tk(), self)
        # Create for future use
        self.state = ""
        self.running = False
        self.player_name = ""
        self.inventory = []

        # Load game data from JSON file
        with open(game_data, mode="rt", encoding="utf-8") as f:
            data = json.loads(f.read())

        self.current_room = data["default_room"]
        self.win_mess = data["win_mess"]
        self.lose_mess = data["lose_mess"]
        self.quit_mess = data["quit_mess"]
        self.intro_mess = data["intro_mess"]
        self.copy_mess = data["copy_mess"]
        self.rooms = data["rooms"]
        self.items = data["items"]  # i.e. target number of items needed to win

        self.states = {
            "title": self.title,
            "intro": self.intro,
            "cmd": self.cmd,
            "moving": self.move_room,
            "getting": self.get_item,
            "using": self.use_item,
            "paused": self.pause,
            "quitting": self.quit
        }

        # Map-specific data
        self.map_data = {}
        self.map_data["room_associations"] = [key for key in self.rooms]
        self.map_data["r"] = ["."]*len(self.map_data["room_associations"])
        self.map_data["map"] = data["map"]

    directions = ("North", "East", "South", "West")
    commands = ("go", "move", "get", "grab", "look", "view", "use", "shoot", "quit", "exit")

    def start(self):
        self.running = True
        self.state = "intro"
        self.title()

    def update(self):
        self.window.update()

    def change_state(self, new_state):
        if new_state == "cmd":
            self.status()
        elif new_state == "paused":
            self.window.prompt.grid_forget()
            self.window.button.config(text="Continue")
            self.window.button.grid(column=0, row=0, padx=0, pady=3)
        self.state = new_state

    def pause(self):
        self.window.prompt.grid(column=0, row=0, padx=0, pady=3)
        self.window.button.grid_forget()
        self.change_state("cmd")

    def quit(self):
        self.window.on_closing()

    # Saves game data to disk in a JSON file
    def save(self):
        saved_game = {
            "player_name": self.player_name,
            "current_room": self.current_room,
            "rooms": self.rooms,
            "inventory": self.inventory
        }
        with open("savedGame.json", mode="wt", encoding="utf-8") as f:
            f.write(json.dumps(saved_game))

    # Loads game data JSON file from disk
    def load(self):
        if exists('savedGame.json'):
            with open('savedGame.json', mode="rt", encoding="utf-8") as f:
                saved_game = json.loads(f.read())
                self.player_name = saved_game["player_name"]
                self.current_room = saved_game["current_room"]
                self.rooms = saved_game["rooms"]
                self.inventory = saved_game["inventory"]
            return True
        else:
            return False

    # Renders the game map
    def mapper(self, room, game_map):
        i = self.map_data["room_associations"].index(room)  # Get index of current room to match against map tiles
        r = self.map_data["r"].copy()  # Room tiles need copied so we don't rewrite them
        r[i] = "@"  # Replace empty tile with player

        return game_map.format(*r)  # *r unpacks the list of room tiles, enabling arbitrary maps

    # Game prompt displays status and takes/returns command
    def status(self):
        for item in self.window.display_frame.winfo_children():
            item.destroy()
        print("*******************************")
        self.window.status_room.config(text=self.current_room, fg="#ffffff")
        print(self.mapper(self.current_room, self.map_data["map"]))
        self.window.status_map.config(text=self.mapper(self.current_room, self.map_data["map"]), fg="#ffffff")
        print("Inventory:", self.inventory)
        self.window.status_inventory.config(text=("Inventory: " + ", ".join(self.inventory)),
                                            wraplength=100, fg="#ffffff")

        self.display("You are in the {}.".format(self.current_room))
        if "item" in self.rooms[self.current_room]:
            self.display("You see a {}.".format(self.rooms[self.current_room]["item"]))
        self.display("Enter your command ('go', 'get', 'look', 'use', 'exit'): ")

    # Displays text in console and GUI
    def display(self, text, width=66, anchor=SW):
        self.window.prompt.focus()
        print(text)
        label = Label(self.window.display_frame, text=text, justify=LEFT, width=width,
                      font=self.window.game_font, anchor=anchor, wraplength=width*10)
        label.grid(column=1, row=len(self.window.display_frame.winfo_children()), sticky=SW)

    # Input parser, used almost universally for input
    def parser(self, multi=True):
        cmd = self.window.prompt.get().split()

        # cmd cannot be empty
        if len(cmd) == 0:
            cmd.append("")

        # Validate cmd input for different numbers of argument (single or multi [default])
        if multi:
            if cmd[0] not in self.commands:
                if cmd[0] != "":
                    self.display("Incorrect command. Try again.")
                else:
                    self.display("No command entered. Try again:")
                    if len(cmd) == 0:
                        cmd.append("")
                self.window.prompt.delete(0, END)
            else:
                if len(cmd) > 1:
                    cmd = [cmd[0], " ".join(cmd[1:]).lower()]
                    cmd[0] = cmd[0].lower()
                    if len(cmd) > 1:
                        cmd[1] = cmd[1].lower()
                else:
                    cmd[0] = " ".join(cmd).lower()
                    cmd[0] = cmd[0].lower()
                    if len(cmd) > 1:
                        cmd[1] = cmd[1].lower()
                return cmd
        else:
            if len(cmd) > 1:
                if cmd[0] in self.commands:
                    cmd.pop(0)
            cmd[0] = " ".join(cmd).lower()
            cmd[0] = cmd[0].lower()
            if len(cmd) > 1:
                cmd[1] = cmd[1].lower()
            return cmd

    # Game title
    def title(self):
        self.display(self.copy_mess, 100, CENTER)
        if not self.load():
            self.display("Enter your name to continue: ", 100)
            self.window.button.grid_forget()
        else:
            self.window.prompt.grid_forget()
            self.window.button.config(text="Start")
            self.display("Welcome back, {name}!".format(name=self.player_name), 100)

    # Game introduction/title/copyright, runs at program start
    def intro(self):
        self.player_name = self.window.prompt.get()
        self.window.prompt.delete(0, END)
        if not self.load() and self.player_name == "":
            self.display("Enter your name to continue: ")
        else:
            for item in self.window.display_frame.winfo_children():
                item.destroy()
            self.display(self.intro_mess.format(name=self.player_name), 100)
            self.display("[Type 'go' and a direction to move. Type 'get' and an item to pick it up. "
                         "Type 'look' to observe look around. "
                         "Type 'use' and an item to use it. Type 'exit' to quit.]\n", 100)
            self.window.prompt.grid(column=0, row=0, padx=0, pady=3)
            self.window.button.grid_forget()
            self.change_state("paused")

    # Take the player's current room and return the room they exit into, if any
    def move_room(self):
        direction = self.parser(False)[0].capitalize()
        self.window.prompt.delete(0, END)

        # Tally valid exits
        exits = []

        for e in self.rooms[self.current_room]:
            if e in self.directions:
                if "required" in self.rooms[self.current_room]:
                    if e == self.rooms[self.current_room]["required"][0]:
                        continue
                    else:
                        exits.append(e)
                else:
                    exits.append(e)

        # Validate input
        if direction not in exits:
            # Handles case where player stops moving
            if direction == "Stay" or direction == "":
                self.display("You decide to stay where you are for now.")
                self.change_state("paused")

            # Handles case where item is required to proceed
            elif "required" in self.rooms[self.current_room]:
                if direction == self.rooms[self.current_room]["required"][0]:
                    self.display(self.rooms[self.current_room]["required"][2])
                elif direction in self.directions:
                    self.display("You find no way out of the {} to the {}.".format(self.current_room, direction))
                else:
                    self.display("'{}' is not a valid direction.".format(direction))
            else:
                if direction in self.directions:
                    self.display("You find no way out of the {} to the {}.".format(self.current_room, direction))
                else:
                    self.display("'{}' is not a valid direction.".format(direction))

            self.display("Enter new direction, or type 'stay' to stay in your room:")
        else:
            self.current_room = self.rooms[self.current_room][direction]
            if "End" in self.rooms[self.current_room]:
                for item in self.window.display_frame.winfo_children():
                    item.destroy()
                if exists('savedGame.json'):  # Delete saved game, win or lose
                    remove('savedGame.json')
                self.display("You are in the {}.".format(self.current_room))
                self.display(self.rooms[self.current_room]["desc"])
                if len(self.inventory) < self.items:
                    self.display(self.lose_mess)
                elif len(self.inventory) == self.items:
                    self.display(self.win_mess)
                self.window.prompt.grid_forget()
                self.window.button.config(text="Continue")
                self.window.button.grid(column=0, row=0, padx=0, pady=3)
                self.change_state("quitting")
            else:
                self.change_state("cmd")

    # Take the player's current inventory and return it with any items found.
    def get_item(self):
        item = self.parser(False)[0]
        self.window.prompt.delete(0, END)

        if "item" in self.rooms[self.current_room]:
            if item != self.rooms[self.current_room]["item"].lower():
                if item == "stop" or item == "":  # Player stops searching
                    self.display("You decide to stop searching the {} for now.".format(self.current_room))
                    self.change_state("paused")
                else:
                    self.display("You search for {} but do not find it in the {}.".format(item, self.current_room))
                self.display("Enter new item to search for, or type 'stop' to cease your efforts:")
            else:
                self.display("You find the {} and stash it in your inventory."
                             .format(self.rooms[self.current_room]["item"]))
                self.inventory.append(self.rooms[self.current_room].pop("item"))
                self.rooms[self.current_room].pop("itemDesc")
                self.change_state("paused")
        else:
            if item == "stop" or item == "":  # Player stops searching
                self.display("You decide to stop searching the {} for now.".format(self.current_room))
                self.change_state("paused")
            else:
                self.display("You search for {} but do not find anything of value in the {}."
                             .format(item, self.current_room))
                self.display("Enter new item to search for, or type 'stop' to cease your efforts:")

    # Takes player input to use inventory items to unlock new rooms
    def use_item(self):
        item = self.parser(False)[0]
        self.window.prompt.delete(0, END)
        inv = [x.lower() for x in self.inventory]

        if item == "stop" or item == "":
            self.display("You decide to stop interacting in the {} for now.".format(self.current_room))
            self.change_state("paused")
        elif item in inv:
            if "required" in self.rooms[self.current_room]:
                if item == self.rooms[self.current_room]["required"][1].lower():
                    self.display(self.rooms[self.current_room]["required"][3])
                    self.rooms[self.current_room].pop("required")
                    self.change_state("paused")
                else:
                    self.display("You find no use for the {} in the {}.".format(item, self.current_room))
                    self.display("Enter new item to use, or type 'stop' to cease your efforts:")
            else:
                self.display("You find no use for the {} in the {}.".format(item, self.current_room))
                self.display("Enter new item to use, or type 'stop' to cease your efforts:")
        else:
            self.display("You do not have the {} in your inventory.".format(item))
            self.display("Enter new item to use, or type 'stop' to cease your efforts:")

    def cmd(self):
        command = self.parser()

        # Run valid commands
        if command is None:
            pass
        elif command[0] == "go" or command[0] == "move":  # Movement
            if len(command) < 2:
                self.display("No direction specified. Please try again:")
                self.window.prompt.delete(0, END)
            else:
                self.change_state("moving")
                self.move_room()
        elif command[0] == "get" or command[0] == "grab":  # Inventory
            if len(command) < 2:
                self.display("No item specified. Please try again:")
                self.window.prompt.delete(0, END)
            else:
                self.change_state("getting")
                self.get_item()
        elif command[0] == "use" or command[0] == "shoot":  # Using
            if len(self.inventory) == 0:
                self.display("There are no items in your inventory to use.")
            else:
                if len(command) < 2:
                    self.display("No item specified. Please try again:")
                else:
                    self.change_state("using")
                    self.use_item()
        elif command[0] == "look" or command[0] == "view":  # Looking
            self.display(self.rooms[self.current_room]["desc"])
            if "itemDesc" in self.rooms[self.current_room]:
                self.display(self.rooms[self.current_room]["itemDesc"])

        elif command[0] == "exit" or command[0] == "quit":  # Quitting
            self.save()
            self.display(self.quit_mess)
            self.window.prompt.grid_forget()
            self.window.button.config(text="Continue")
            self.window.button.grid(column=0, row=0, padx=0, pady=3)
            self.change_state("quitting")
        else:  # Failsafe; shouldn't be triggered
            print("Invalid input. Try again.")
