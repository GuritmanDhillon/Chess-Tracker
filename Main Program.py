import time
from winotify import Notification, audio # notification service
from selenium import webdriver # emulates a webpage and uses that to scan chess.com's html code
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
# from win10toast import ToastNotifier # notification service [BROKEN]
import customtkinter as ctk # used for the GUI
import threading # for running programs in the background (prevents the window from freezing while the program runs)
from PIL import Image
import requests
from io import BytesIO


# HyperParameters:
#----------------------------------------
SLEEP_TIME = 60
# USERNAME = "Hikaru"
square_size = 60 # size of the tiles
#----------------------------------------

options = Options()
options.add_argument("--headless")

# UI features
ctk.set_appearance_mode("dark")
app = ctk.CTk()
app.geometry("600x300")
app.resizable(False, False)
app.title("Improved Chess Detector")
for i in range(11):
    app.grid_rowconfigure(i, weight=1)
    app.grid_columnconfigure(i, weight=1)


label = ctk.CTkLabel(app, text="Enter Chess.com Username:")
label.grid(row=0,column=5)

entry = ctk.CTkEntry(app, placeholder_text="e.g., MagnusCarlsen")
entry.grid(row=1,column=5)

# define the ChromeDriver service first
service = Service()  # optional: add executable_path="path/to/chromedriver" if needed
obtained = False
wasOnline = False
isRunning = False
closed = False
statusLabel = ctk.CTkLabel(app, text="")
username = ""
oldUsername = ""

# open Chrome
def mainProgram():
    # make sure these are global, otherwise python assumes they are local to the function
    global wasOnline, obtained, isRunning, username, oldUsername
    
    button.configure(state="disabled")
    
    username = entry.get()
    
    # if you press the stop and start button too quickly, two instances can run at the same time
    # before one closes
    
    if isRunning:
        return
    
    isRunning = True
    # used to stop the program on command
    
    
    # ctk.CTkLabel(app, text="Tracking...").pack()
    
    tracking.configure(text="Tracking...")
    
    # runs unless its told to stop by an external source
    while isRunning:

        with webdriver.Chrome(service=service, options=options) as driver:
            statusLabel.configure(text=f"Tracking {username}...")
            driver.get(f"https://www.chess.com/member/{username}")
            print(driver.title)
            if driver.title == "Missing Page - Chess.com":
                statusLabel.configure(text="User could not be found")
            paragraphs = driver.find_elements(By.CLASS_NAME, "profile-header-details-item")
            obtained = False
            for p in paragraphs:
                # doesnt repeat if I already got what I needed
                if obtained:
                    break

                if p.text.strip().startswith("Last Online"):
                    statusLabel.configure(text=p.text)
                    print(p.text)
                    obtained = True
                    if wasOnline:
                        toast = Notification(
                            app_id="Chess Detector",
                            title="Status Update",
                            msg=f"{username} is no longer online",
                            duration="short"
                        )
                        toast.set_audio(audio.Default, loop=False)
                        toast.show()
                        wasOnline = False
                elif p.text.strip().startswith("Online now"):
                    statusLabel.configure(text=p.text)
                    print(p.text)
                    obtained = True
                    if not wasOnline:
                        toast = Notification(
                            app_id="Chess Detector",
                            title="Status Update",
                            msg=f"{username} is {p.text}",
                            duration="short"
                        )
                        toast.set_audio(audio.Default, loop=False)
                        toast.show()
                    wasOnline = True
        
        for i in range(SLEEP_TIME, 0, -1):
            # this program ends it without creating errors if the windows closed
            if closed:
                break
            if not isRunning:
                tracking.configure(text="")
                statusLabel.configure(text="")
                break
            tracking.configure(text=f"Checking again in {i} seconds...")
            print(f"\rChecking again in {i} seconds...   ")
            time.sleep(1)
            getUserData(username)
            print(f"Currently {len(threading.enumerate())} threads alive")
            # ends the program if multiple threads are running at the same time, there
            # should only be 2 at a time
            if len(threading.enumerate()) >= 3:
                return
        print("\nChecking...")
        

def endLoop():
    global isRunning
    isRunning = False
    tracking.configure(text="")
    statusLabel.configure(text="")
    button.configure(state="enabled")
    gameStatus.configure(text="")

def onClosing():
    global isRunning, closed
    closed = True
    isRunning = False
    app.destroy()


# Function to scrape latest moves
def getUserData(username):
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                      "AppleWebKit/537.36 (KHTML, like Gecko) "
                      "Chrome/138.0.0.0 Safari/537.36"
    }
    
    archives_url = f"https://api.chess.com/pub/player/{username}/games/archives"
    res = requests.get(archives_url, headers=headers)
    if res.status_code != 200:
        print("Failed to fetch archives", res.status_code)
        return None
    
    archive_urls = res.json().get("archives", [])
    if not archive_urls:
        print("No archives found")
        return None

    # Step 1: Find the latest archive that exists
    latest_archive_url = None
    for url in reversed(archive_urls):
        res = requests.get(url, headers=headers)
        if res.status_code == 200:
            latest_archive_url = url
            break

    if latest_archive_url is None:
        print("No valid archive found")
        return None

    # Step 2: Fetch latest archive
    res = requests.get(latest_archive_url, headers=headers)
    data = res.json()["games"]
    games = res.json().get("games", [])
    if not games:
        print("No games in this archive")
        return None
    
    # This is to grab the profile picture
    res2 = requests.get(f"https://api.chess.com/pub/player/{username}", headers=headers)
    data2 = res2.json()
    pfpURL = data2.get("avatar") # this is the .jpg link
    
    if pfpURL:
        imgData = requests.get(pfpURL).content
        img = Image.open(BytesIO(imgData))
        
        # img = img.resize((100, 100))
        
        # convert the pillow image to a Ctk image
        ctkImg = ctk.CTkImage(light_image=img, dark_image=img, size=(100, 100))
        if not closed:
            profileLabel.configure(image=ctkImg)
            profileLabel.image = ctkImg
    else:
        print("No profile picture found")
    
    # this part just organizes the data and outputs it
    # I only selected some of the data, some of the other stuff is unimportant
    white = data[-1]["white"]
    black = data[-1]["black"]
    opening = data[-1]["eco"]
    opening = opening.split("/")[-1]
    opening = opening.split(".")[0]
    opening = opening.replace("-", " ")
    if white["username"] == username and not closed and isRunning:
        gameStatus.configure(text=f"Current {data[-1]["time_class"]} Rating: {white["rating"]}\n"
                             f"Last Match Results: {f"win by {black["result"]}" if white["result"] == "win" else f"loss by {white["result"]}"} against {black["username"]}\n"
                             f"Opening: {opening}")
    elif not closed and isRunning: # skipping the check for (not closed) gives an error when closing the window, program doesnt end nicely as a result
        gameStatus.configure(text=f"Current {data[-1]["time_class"]} Rating: {black["rating"]}\n"
                             f"Last Match Results: {f"win by {white["result"]}" if black["result"] == "win" else f"loss by {black["result"]}"} against {white["username"]}\n"
                             f"Opening: {opening}")

button = ctk.CTkButton(app, text="Start Tracking", command=lambda: threading.Thread(target=mainProgram).start(),
                       fg_color="#69923e", hover_color="#4e7837")

endbutton = ctk.CTkButton(app, text="End Tracking", command=lambda: threading.Thread(target=endLoop).start(),
                        fg_color="#4b4847", hover_color="#2c2b29")

tracking = ctk.CTkLabel(app, text="")
gameStatus = ctk.CTkLabel(app, text="")

# this allows the profile picture to have something as a placeholder
# I just used a chessboard from the chess.com website
url = "https://images.chesscomfiles.com/uploads/v1/images_users/tiny_mce/lularobs/phpQJWmL4.png"  # PNG queen
headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                  "AppleWebKit/537.36 (KHTML, like Gecko) "
                  "Chrome/138.0.0.0 Safari/537.36"
}
# this makes sure that the program is connected to wifi on initialization,
# if not, it closes everything.
# what happens if the wifi cuts out while its running you ask? The program crashes.
# I am not making a check for that, its too much work, honestly, but I would just need to use
# a bunch of try statements, amybe if I try to work on the code in the future, but
# every other possible bug/user error should be accounted for now.
try:
    res = requests.get(url, headers=headers)
    img = Image.open(BytesIO(res.content))
    img = img.resize((100, 100))
    chess_piece_img = ctk.CTkImage(light_image=img, dark_image=img, size=(100, 100))
    profileLabel = ctk.CTkLabel(app, image=chess_piece_img, text="")
    profileLabel.configure(image=chess_piece_img)
    profileLabel.image = chess_piece_img

    # this just organizes everything
    button.grid(row=3,       column=5)
    endbutton.grid(row=4,    column=5)
    statusLabel.grid(row=2,  column=1) # this helps keep the elements in order on initialization
    tracking.grid(row=5,     column=5)
    gameStatus.grid(row=3,   column=1)
    profileLabel.grid(row=2, column=5)
except requests.exceptions.ConnectionError:
    print("No internet connection detected. Please check your WiFi.")
    label.configure(text="No internet connection detected. Please check your WiFi.\n Please close the application and try again.")
except requests.exceptions.Timeout:
    print("Request timed out. Maybe the network is slow.")
    label.configure("Request timed out. Maybe the network is slow.\n Please close the application and try again.")
except requests.exceptions.HTTPError as e:
    print(f"HTTP error occurred: {e}")
    label.configure(f"HTTP error occurred: {e}\n Please close the application and try again.")
except Exception as e:
    print(f"Some other error occurred: {e}")
    label.configure(f"Some other error occurred: {e}\n Please close the application and try again.")

app.protocol("WM_DELETE_WINDOW", onClosing)

app.mainloop()
