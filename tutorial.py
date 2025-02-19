"""
we are using telegram for now, this is the working telegram handler script `telegram_handler.py`

our gemini ai handling comes from `gemini_process.py`


- this will utilize telegrams recording of the ogg audio data for the full process 

This is the sequence we have in mind over the following steps:

# call from client to process audio and prompt_type `name_input`; generate results with `name_input` response structure
# call from client to process intial audio, `name_input` results and prompt_type `name_corrections`; generate results with `name_corrections` response structure
# call from client to process audio files (inital & truthnlie) and prompt_type `truthnlie` response structure 


now the sequence with telegram in mind:

1. user connects to bot
2. user sends /start {first message}

### user name input begins ###

3. bot sends welcome message inviting the user to introduce themself with a greating i.e. the user is expected to say `hi, my name is full complete name and even any nicknames they might go by` this is recorded via audio and shared as a voice memo.{second and third message}

NOTE: *on GEMINI results* the bot sends a message in response to the audio memo
(the prompt_type will determine the output and unfortunately in this medium of telegram the json output is not supported so we will need to process the results before sending them to the client)

4. The bot sends a message to the user asking them to say `yes` or `no` if the bot has captured their name, and adds additional interesting maybe controversial or interesting the ai could infer such a thing from the audio memo. 
### name correction ###

4.5. if the user says `no`, then the bot sends a message asking the user to type there actual name that they spoken in the audio memo.

### truthnlie ###

5. On whenever name is correct,then the user is prompted to begin a truth n lie session. they are told to speak three statements in an audio memo, one a lie and two truths. 
6. the bot sends the result including reasoning, and the user is prompted to say `yes` or `no` if the bot has captured their truth n lie. 

### truthnlie correction ###

7. if `no` is said then the results of the inital truthnlie are sent again in another gemini request including the original audio for the truth n lie. 

### profile creation ### 

8. Now that the user has completed the name_input & truth n lie session and any model corrections, the bot sends a message to the user making inferences and insights its gathered into the user encouraging them to share the bot with a friend and to waitlist for my app. 
- ideally we saved the results to a database and the user can access them via the web app and also they can choose to share the result with a friend.
The provided code snippet is a documentation block from a Python script named tutorial.py. It appears to describe a planned or existing implementation for a bot that interacts with users through Telegram, utilizing audio data for various processes. Here's a breakdown of the main concepts and flow described:

Overview:
Libraries and Scripts: The bot interacts with users using Telegram, and processes audio using functionality defined in two separate scripts: telegram_handler.py and gemini_process.py.
Audio Data: The interaction primarily uses audio data, specifically in the OGG format, for processing user input and generating responses.
Sequence of Interaction:
Connection and Introduction:

The user initiates a conversation with the bot by sending a /start command.
The bot sends a welcome message prompting the user to introduce themselves by stating their full name and any nicknames via an audio memo.
The bot processes the audio data using an AI system (referred to as "GEMINI") to capture the user's name and provide feedback.
Name Confirmation and Correction:

The bot asks the user to confirm whether it captured their name correctly with a simple yes or no.
If the user responds with no, the bot requests the user to type in their name for correction.
Truth and Lie Session:

Once the user's name is confirmed, the bot invites the user to engage in a "truth n lie" session, where they provide an audio memo with three statements (one false and two true).
The bot analyzes these statements and sends the user the inferred results, asking for confirmation.
Correction of Truth and Lie Results:

If the initial truth and lie results are incorrect according to the user, the bot makes another request to refine the results using the original audio data.
Profile Creation:

After successfully capturing and confirming the user's name and truth and lie game, the bot compiles gathered insights into a user profile.
It encourages users to engage further, such as sharing the bot with friends or joining a waitlist for an app.
Data Handling and Storage:
The results are intended to be saved in a database, indexed, and perhaps shared via a web app.
Audio files are stored in an S3 bucket, which is a cloud storage service.
Important Concepts:
AI Processing: The bot uses an AI system (GEMINI) to process audio data and extract meaningful information which determines the flow of conversation.
User Interaction: The interaction relies heavily on voice inputs that are converted and processed for understanding through AI.
Data Storage and Retrieval: The audio and derived insights are stored and structured for future access and user interaction optimization.
In summary, this documentation outlines the design and function of a Telegram bot that interacts with users through audio inputs, processes these inputs using AI, confirms and corrects data through user feedback, and stores insights for enhanced user engagement.


"""

# save results as user profile

# index embeddings of results
# - map to user profile

# rank similarities of results and process (audio files and results) of similar users
# - audi files are saved to s3 bucket
