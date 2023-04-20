class Lessons:
    @staticmethod
    def pintro():
        return [
            "Welcome to an unnoficial guide of *How to use Python3*, in Discord!\n\nThis guide is maintained by "
            "`Predeactor#0495`, any useful report can be reported to me, there's also the [repository of this Cog]("
            "https://github.com/Predeactor/Predeactor-Cogs) if you want to help me in writing this little guide *if* "
            "you already know Python.\n```I want to test my code in Discord!```\nThis is a possible thing if the bot "
            "your talking with is your. [This bot is an instance of Red, an open source Python bot]("
            "https://github.com/Cog-Creators/Red-DiscordBot), if the bot is not your, you can follow the link to host a"
            " bot at your own (Don't worry, it's easy to setup and use :3). When starting up your bot, you can parse "
            "the `--dev` argument, but if you use the mock cog, you can install the cog `dev` from [TrustyJAID's repo]("
            "https://github.com/TrustyJAID/Trusty-Cogs) and load it.\nNow that we have dev loaded, use `[p]repl` (Where"
            " `[p]` is your prefix), it's like the Python interpreter, but in Discord!\n\nTo use the Python interpreter"
            ", you must start your command with ` and you can now start learning!.\n\nEverything is setup, enjoy me "
            "lessons!\n- *Made by Predeactor.* "
        ]

    @staticmethod
    def pref():
        return [
            "Those links are from the Red - Discord Bot server, thank to them for those sweet links!",
            3,
            "```New to programming:```\n[CodeCademy](https://codecademy.com/) (Free interactive courses for "
            "fundamentals)\n[A Byte of Python](https://python.swaroopch.com/) (For complete beginners to programming, "
            "also my recommendation)\nSee also: [CodeAbbey](http://www.codeabbey.com/) (Exercises for beginners)\n["
            "learnpython.org](https://www.learnpython.org/) (somewhat interactive tutorial)\n\n```For who already know "
            "programming:```\n[Learn X in Y minutes, Where X=Python](https://learnxinyminutes.com/docs/python3/) (For "
            "who "
            "know programming already)\n[Official Python Documentation, The Python Tutorial]("
            "https://docs.python.org/3/tutorial/) (For the in-between group, i.e. knows some programming but not a "
            "lot)\n\n```Youtube Videos```\n[Python Programming Begginer Tutorials, by Corey Schafer]("
            "https://www.youtube.com/playlist?list=PL-osiE80TeTskrapNbzXhwoFUiLCjGgY7)\n[Python Tutorials, "
            "by Corey Schafer](https://www.youtube.com/playlist?list=PL-osiE80TeTt2d9bfVyTiXJA-UTHn6WwU)\n[Python OOP "
            "Tutorials - Working with Classes, by Corey Schafer]("
            "https://www.youtube.com/playlist?list=PL-osiE80TeTsqhIuOqKhwlXsIBIdSeYtc)",
        ]

    @staticmethod
    def plvl1():
        return [
            "Hello there, and let me say, WELCOME, welcome to your first lesson of *How to use Python3*, wonderful! "
            "You're learning right in Discord, isn't it awesome?\n\nI'm Predeactor, I'll be your teacher for now\n\nSo "
            "let's start with installing Python.\nYou are running this command from Red, an open source Discord Bot "
            "written in Python, so I think you already had Python installed on your system. However, if you need to "
            "install Python, you can go to the official Python website to download Python : "
            "https://www.python.org/downloads/.\nNot on Windows? Using Linux? You can use the command `sudo apt-get "
            "install python3`.",
            20,
            "```My First Command```\nNow that you installed Python, let's start with your first command!\nWe're gonna "
            "start Python, the easiest way is, opening your terminal and typing `python`\n\n```I'm sorry but I don't "
            "know what is a terminal...```\nNo worry, everyone start somewhere! You can take a look at this : "
            "https://askubuntu.com/a/38220.\nReady? You should see something like this : \n```python\nPython 3.X.X "
            "(Some "
            'informations)\nType "help", "copyright", "credits" or "license" for more information.\n>>>```\nWelcome to '
            "your Python Interpreter, where you can test codes, and where `>>>` will be your command.\nNow that we "
            'started Python, we\'re gonna show something in this empty terminal. Type `print("My super text")`, '
            "done? Hit Enter and WOAH! You just showed your super text into your terminal using a function, but what is"
            " a "
            "function? I will tell you later ;)\n\nYou made it! You succesfully launched Python and ran your first "
            "command, in the next lesson, we will talk about variable, those magic things!\n\n*Nb: To close your Python"
            " interpreter, just close the window or type `exit()` ;)*",
        ]

    @staticmethod
    def plvl2():
        return [
            "```My First Variable```\nWelcome to your next lesson, let's discover together what a variable is\n\nA "
            "variable is an attibution of a data. Let me explain you with an example:\n\t- When you're playing "
            "Minecraft "
            "and need to find easily your stuff in your chest, you will put a sign on the chest with whatyour chest "
            "contain, like `Foods`, and inside the chest, you got all of your delicious food, cooked porks, rabbits, "
            "and more...\n\t- When you're cleaning your chamber and have to store everything, you want to separate your"
            " books of history the from your books of physics, then you use 2 box, a `History` box, where there's all "
            "of "
            "your history books, and another one box called `Science` where there's every science books. (Explaining "
            "made "
            "easy :'))\n\nI hope I didn't lose you.",
            30,
            "Now, you want to make your first variable, but how ? We use the `=` sign to define the variable. Start "
            "your "
            "Python interpreter. We're gonna start by defining what the sound of the dog, the dog's sound is \"Waf!\", "
            'maybe not, but that\'s just an example...\n\nNow type `dog_sound = "Waf"`, here, we define the variable '
            "dog_sound to \"Waf\", you're maybe wondering why we're using double quotes, that's because we define a "
            "*string*, if we don't, we're defining a variable inside a variable, it can be useful sometime, but "
            "defining "
            "a variable of a variable is useless.\n\nNow that we have our variable, we want to show it, right? Let's "
            "type "
            "the variable name now, follow my example:\n```python\n>>> dog_sound\n'Waf'```\nWhat we do is showing up "
            "the "
            "variable's content, awesome! Now you know how to define a variable and how to access it!\n\nTheory for "
            "now: "
            "we will see the different type of data in the next lesson.",
        ]

    @staticmethod
    def plvl3():
        ignored_double_quote = '\\"'
        return [
            f"```The different Type of Data```\nToday, we're gonna see some theory, yes, don't expect any code today!\n"
            f"There's different types of data in Python, AND NOT only in Python, that would be a mess without that.",
            7,
            f"\n\n> **String**\nString is text, text is string. To define a string, you use two times single (') or "
            f"double quotes (\"), inside those quotes, you put inside your text, that's your string!\nE.g: `'My string "
            f"is "
            f"awesome'`, `\"I love strings!\"`\n\n:warning: **If you want to use a double quote into a string who's "
            f"using "
            f"double quote, you need to tell Python you want your double quote ignored! For that, before your double "
            f"quote (The one you want ignored), put \\, like this `{ignored_double_quote}` **\n\n> **Integrer**\n"
            f"Integrer "
            f"are numbers. They don't need anything, just a number.\nE.g: `secret_password = 8869`\n:pushpin: A number "
            f"and a number in a string is different, we will get into math later.\n> **Float**\nA float is a number "
            f"with "
            f"a ploating point/coma.\nE.g: `float = 3.998`\n:pushpin: You cannot convert a float into integrer, "
            f"but you can into string.\n> **Boolean**\nBoolean are one of the most important thing in Python, "
            f"there's 2 types of booleans, `True` and `False`, those are VERY important AND, please, keep them "
            f"somewhere "
            f"in your mind.",
            30,
            "Time for congratulation ! Now you know what is what in Python! Next time, we will talk about comparators.",
        ]
