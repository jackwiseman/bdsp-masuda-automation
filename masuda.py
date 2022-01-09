import time
import json
import os

from src.utils import *
from src.notify import send_message

import numpy as np
from PIL import Image
import nxbt

# find the position of the cursor in the box by taking a screenshot, converting it
# to greyscale and checking predetermined slices where the cursor can show up, finding
# the slice which contains the pixel closest to white
def get_box_coords(debug=False):
    img = get_image()
    img = np.dot(img[...,:3], [.3, .6, .1]) # convert to greyscale

    OFFSET_X = 52 # step size in x direction
    OFFSET_Y = 62 # step size in y direction
    pos = (0,0)
    largest = 0.0 # ensure a result will be found

    # check the party first
    for row in range(6):
        party = img[89+(61*row):94+(61*row), 35:42]
        if(debug):
            print("(-1, " + str(row) + ") - " + str(party.max()))
        if(party.max() > largest):
            largest = party.max()
            pos = (-1, row)
 
    # iterate over the box
    # requires "Simple" wallpaper and multiselect on
    for col in range(6):
        for row in range(5):
            candidate = img[95+(OFFSET_Y*row):99+(OFFSET_Y*row), 202+(OFFSET_X*col):208+(OFFSET_X*col)] 
            if(debug):
                print("(" + str(col) + ", " + str(row) + ") - " + str(candidate.max()))
            if(candidate.max() > largest):
                largest = candidate.max()
                pos = (col, row)
    return pos

# return an array of all positions that are currently highlighted using multiselect
# done by checking a small area above each icon and testing the green values to see
# if they are greater than a threshold
def get_selected_coords(debug=False):
    img = get_image()
    OFFSET_X = 52 # step size in x direction
    OFFSET_Y = 62 # step size in y direction
    threshold_box = 239.0 # THIS HAS BEEN RECENTLY CHANGED FROM 240
    threshold_party = 200.0
    selected = []

    # check party
    for row in range(6):
        candidate = img[122+(OFFSET_Y*row):129+(OFFSET_Y*row), 143:150] 
        max_green_val = candidate[ :, :, 1].max()
        if(debug):
            print(f"(-1, {row}): {max_green_val}")
        if max_green_val > threshold_party:
            selected.append((-1, row))

    # check box
    for col in range(6): #these may need to be switched in order to get first appearance
        for row in range(5):
            candidate = img[109+(OFFSET_Y*row):111+(OFFSET_Y*row), 194+(OFFSET_X*col):197+(OFFSET_X*col)] 
            max_green_val = candidate[ :, :, 1].max()
            if(debug):
                #save_array_as_image(candidate, f"{row}")
                print(f"({col}, {row}): {max_green_val}")
            if max_green_val > threshold_box:
                selected.append((col, row))
    return selected

# Find the position of the picked up pokemon by converting the image to greyscale, parsing predetermined slices
# of the screenshot and returning the first slice to surpass the white threshold, false if none are found
def get_picked_up_coords(debug=False):
    img = get_image()
    img = np.dot(img[...,:3], [.3, .6, .1]) # convert to greyscale
    box_selection = [192, 196, 96, 100] # base box crop, not sure if I want to keep this, but reduces magic numbers below
    party_selection = [20, 24, 80, 82]
    OFFSET_X = 52 # step size in x direction
    OFFSET_Y = 62 # step size in y direction
    box_threshold = 230
    party_threshold = 210

    # check party
    for row in range(6):
        candidate = img[party_selection[2]+(OFFSET_Y*row):party_selection[3]+(OFFSET_Y*row), party_selection[0]:party_selection[1]]
        max_white = candidate.max()
        if(debug):
            print(f"(-1, {row}: {max_white}")
        if(max_white > party_threshold):
            return (-1, row)

    # check box
    for row in range(5): # row goes first so that we can return the FIRST instance of > white threshold
        for col in range(6):
            candidate = img[box_selection[2]+(OFFSET_Y*row):box_selection[3]+(OFFSET_Y*row), box_selection[0]+(OFFSET_X*col):box_selection[1]+(OFFSET_X*col)]
            max_white = candidate.max()
            if(debug):
                print(f"({col}, {row}: {max_white}")
            if(max_white > box_threshold):
                return (col, row)
    return False

def is_selected(coord):
    return coord in get_selected_coords()

def move_to_nursery_man(nx, controller_index):
    menu_open_check = np.array(Image.open("./check-imgs/menu_open.png"))
    fence_corner_check = np.array(Image.open("./check-imgs/left_1_ref.png"))
    fence_second_corner_check = np.array(Image.open("./check-imgs/up_1_ref.png"))
    inline_ref = np.array(Image.open("./check-imgs/inline_with_man_ref.png"))

    # FLY TO SOLACEON
        # press X until in menu 
    menu_view = False
    while (menu_view == False):
        nx.press_buttons(controller_index, [nxbt.Buttons.X], up=1.0)
        img = get_image()
        img_mse = mse(menu_open_check, img)
        #print(img_mse)
        if img_mse < 65:
            menu_view = True
            break

    while(True):
        nx.press_buttons(controller_index, [nxbt.Buttons.DPAD_RIGHT], up=1.0)
        img = get_image()[186:192, 143:149]
        img = np.dot(img[...,:3], [.3, .6, .1]) # convert to greyscale
        if(img.max() > 215):
            # spam A to fly to Solaceon town (assumes we're already here)
            for i in range(7):
                nx.press_buttons(controller_index, [nxbt.Buttons.A], up=1.0)
            break
#
    # move to corner of fence

    reached_first_fence = False
    while(reached_first_fence == False):
        nx.press_buttons(controller_index, [nxbt.Buttons.DPAD_LEFT], up=1.0)
        img = get_image()[198:237, 294:323]
        img_mse = mse(img, fence_corner_check)
        print(img_mse)
        if img_mse < 80:
            reached_first_fence = True
            break

    # move to top corner of fence (just below man)
    reached_second_fence = False
    while(reached_second_fence == False):
        nx.press_buttons(controller_index, [nxbt.Buttons.DPAD_UP], up=1.0)
        img = get_image()[248:279, 286:317]
        img_mse = mse(img, fence_second_corner_check)
        print(img_mse)
        if img_mse < 80:
            reached_second_fence = True
            break

    # no need to check images here, just spam the dpad_left to make sure we're against the left fence, although checking will probably speed it up
    for i in range(3):
        nx.press_buttons(controller_index, [nxbt.Buttons.DPAD_LEFT], down=2.0)

    # move so that we're in the same line as the old man
    inline = False
    while(inline == False):
        nx.press_buttons(controller_index, [nxbt.Buttons.DPAD_UP], up = 1.0)
        img = get_image()[168:203, 404:439]
        img_mse = mse(img, inline_ref)
        print(img_mse)
        if img_mse < 20:
            inline = True
            break

def move_to_bike_path(nx, controller_index):
    menu_open_check = np.array(Image.open("./check-imgs/menu_open.png"))
    bike_path_ref = np.array(Image.open("./check-imgs/bike_path_ref.png"))
    # FLY TO SOLACEON
        # press X until in menu 
    menu_view = False
    while (menu_view == False):
        nx.press_buttons(controller_index, [nxbt.Buttons.X], up=1.0)
        img = get_image()
        img_mse = mse(menu_open_check, img)
        #print(img_mse)
        if img_mse < 65:
            menu_view = True
            break

    while(True):
        nx.press_buttons(controller_index, [nxbt.Buttons.DPAD_RIGHT], up=1.0)
        img = get_image()[186:192, 143:149]
        img = np.dot(img[...,:3], [.3, .6, .1]) # convert to greyscale
        if(img.max() > 215):
            # spam A to fly to Solaceon town (assumes we're already here)
            for i in range(7):
                nx.press_buttons(controller_index, [nxbt.Buttons.A], up=1.0)
            break
    #

    on_bike_path = False
    while (on_bike_path == False):
        nx.press_buttons(controller_index, [nxbt.Buttons.DPAD_LEFT], up=1.0)
        img = get_image()[137:172, 501:536]
        img_mse = mse(bike_path_ref, img)
        print(img_mse)
        if img_mse < 65:
            on_bike_path = True
            break

def init_bookends():
    img = get_image()[124:132, 205:213]
    array = img.swapaxes(0,1) 
    as_image = pygame.pixelcopy.make_surface(array)
    filename = 'check-imgs/bookend.png'
    pygame.image.save(as_image, filename)
    

def init_breed_species():
    img = get_image()[124:132, 205:213]
    array = img.swapaxes(0,1) 
    as_image = pygame.pixelcopy.make_surface(array)
    filename = 'check-imgs/breedspeecies.png'
    pygame.image.save(as_image, filename)

#def picked_up():
#    return get_picked_up_coords() != False

def move_to(dst, nx, controller_index, picked_up=False):
    if(picked_up == False):
        while(get_box_coords()[0] != dst[0]):
            if get_box_coords()[0] < dst[0]:
                nx.press_buttons(controller_index, [nxbt.Buttons.DPAD_RIGHT], up=1.0)
            else:
                nx.press_buttons(controller_index, [nxbt.Buttons.DPAD_LEFT], up=1.0)
        while(get_box_coords()[1] != dst[1]):
            if get_box_coords()[1] < dst[1]:
                nx.press_buttons(controller_index, [nxbt.Buttons.DPAD_DOWN], up=1.0)
            else:
                nx.press_buttons(controller_index, [nxbt.Buttons.DPAD_UP], up=1.0)
    else:
        while(get_picked_up_coords(debug=True)[0] != dst[0]):
            if get_picked_up_coords()[0] < dst[0]:
                nx.press_buttons(controller_index, [nxbt.Buttons.DPAD_RIGHT], up=1.0)
            else:
                nx.press_buttons(controller_index, [nxbt.Buttons.DPAD_LEFT], up=1.0)
        while(get_picked_up_coords(debug=True)[1] != dst[1]):
            if get_picked_up_coords()[1] < dst[1]:
                nx.press_buttons(controller_index, [nxbt.Buttons.DPAD_DOWN], up=1.0)
            else:
                nx.press_buttons(controller_index, [nxbt.Buttons.DPAD_UP], up=1.0)

# move box view to first page available
def first_page(nx, controller_index):
    bookend_check = np.array(Image.open("./check-imgs/bookend.png"))

    found_bookend = False
    while(found_bookend == False):
        nx.press_buttons(controller_index, [nxbt.Buttons.L], up=2.0)
        img = get_image()[124:132,205:213]
        img_mse = mse(bookend_check, img)
        print(img_mse)
        if img_mse < 10:
            found_bookend = True
            break

    while(found_bookend == True):
        nx.press_buttons(controller_index, [nxbt.Buttons.R], up=2.0)
        img = get_image()[124:132,205:213]
        img_mse = mse(bookend_check, img)
        print(img_mse)
        if img_mse > 10:
            found_bookend = False
            break
            
# move box view to last page available
def last_page(nx, controller_index):
    bookend_check = np.array(Image.open("./check-imgs/bookend.png"))

    found_bookend = False
    while(found_bookend == False):
        nx.press_buttons(controller_index, [nxbt.Buttons.R], up=2.0)
        img = get_image()[124:132,205:213]
        img_mse = mse(bookend_check, img)
        print(img_mse)
        if img_mse < 10:
            found_bookend = True
            break

    while(found_bookend == True):
        nx.press_buttons(controller_index, [nxbt.Buttons.L], up=2.0)
        img = get_image()[124:132,205:213]
        img_mse = mse(bookend_check, img)
        print(img_mse)
        if img_mse > 10:
            found_bookend = False
            break

# assumes you are are standing to the left of the man
def get_new_eggs(num_eggs, nx, controller_index, stats):
    egg_check = np.array(Image.open("./check-imgs/egg-ref.png"))
    man_talking_check = np.array(Image.open("./check-imgs/man_talking_check.png"))
    eggs_recieved = 0
    egg_ready = False
    i = 0
    while(eggs_recieved < num_eggs):
        nx.press_buttons(controller_index, [nxbt.Buttons.DPAD_LEFT], down=1.0, up=0.2)
        nx.press_buttons(controller_index, [nxbt.Buttons.R], down=1.0, up=0.2)
        img = get_image()[104:124,601:618]
        img_mse = mse(img, egg_check)
        #print(img.max())
        if img_mse < 10:
#        if img.max() > 135:# should be lower to account for night
            # egg found
            nx.press_buttons(controller_index, [nxbt.Buttons.DPAD_RIGHT], down=1.0)

            print("spam A until the man asks if we want the egg")
            egg_confirmation = False
            while(egg_confirmation == False):
                nx.press_buttons(controller_index, [nxbt.Buttons.A], up=0.5)
                img = np.dot(get_image()[334:344,570:580][...,:3], [.3, .6, .1])
                #print(img.max())
                if img.max() > 200: 
                    egg_confirmation = True
                    break

            print("spam A until the man asks us to take good care of it (ie pokemon nursery man title comes back up)")
            take_good_care = False
            while(take_good_care == False):
                nx.press_buttons(controller_index, [nxbt.Buttons.A], up=0.5)

                candidate = get_image()[365:384, 160:309]
                save_array_as_image(get_image(), "wtfisgoingon")
                img_mse = mse(man_talking_check, candidate)
                #print(img_mse)
                if img_mse < 10 : # because the image is so 
                    take_good_care = True
                    break

            print("spam A until this goes away, continue")
            while(take_good_care == True):
                nx.press_buttons(controller_index, [nxbt.Buttons.A], up=0.5)
                candidate = get_image()[365:384, 160:309]
                img_mse = mse(man_talking_check, candidate)
                #print(img_mse)
                if img_mse > 10:
                    take_good_care = False
                    break
            stats["eggs"] += 1
            eggs_recieved += 1
            continue

        else:
            nx.press_buttons(controller_index, [nxbt.Buttons.DPAD_RIGHT], down=1.0)


# intended to be used when all boxes are fully hatched, ie there are no eggs or empty spaces
# use with caution as this is mostly untested
# essentially a "reset"
def release_boxes(nx, controller_index): # add num_boxes arg
    box_menu_check = np.array(Image.open("./check-imgs/box_menu_check.png"))
    release_select_check = np.array(Image.open("./check-imgs/release_select_check.png"))
    release_confirmation_check = np.array(Image.open("./check-imgs/release_confirmation_check.png"))
    release_textbox_check = np.array(Image.open("./check-imgs/release_textbox_check.png"))
    breed_speecies_check = np.array(Image.open("./check-imgs/breedspecies.png"))
    bookend_check = np.array(Image.open("./check-imgs/bookend.png"))

    # go to first page
    first_page(nx, controller_index)

    # move to next box with intended breed pokemon in slot (0,0)
    # TODO: reduce magic numbers, tie in img resolutions with init functions
    pokemon_at_0_pos = get_image()[124:132, 205:213]
    while mse(bookend_check, pokemon_at_0_pos) > 10: # while we haven't reached the end
        if mse(breed_speecies_check, pokemon_at_0_pos) > 10: # empty space found, skip this box
            print("skip!")
            nx.press_buttons(controller_index, [nxbt.Buttons.R],up=2.0)
            pokemon_at_0_pos = get_image()[124:132, 205:213] # update view
        else:
            print("gotta do something")
            for col in range(6):
                for row in range(5):
                    # can speed this up a few seconds by "snaking" around the box
                    move_to((col, row), nx, controller_index)

        #            # Decide if there's a pokemon here
        #
        #            img = get_image()[124+(62*row):132+(62*row), 205+(52*col):213+(52*col)]
        #            img_mse = mse(breed_speecies_check, img)
        #            print(f"({col}, {row}): {img_mse}")
        #            if img_mse > 120:
        #                print("There's no pokemon here!")
        #                continue

                    # Open the box action menu
                    box_menu_open = False
                    while(box_menu_open == False):
                        nx.press_buttons(controller_index, [nxbt.Buttons.A], up=1.2)
                        img = get_image()[200:374, 461:594]
                        img_mse = mse(box_menu_check, img)
                        if img_mse < 25:
                            box_menu_open = True
                            break
                    
                    # move arrow until 'release' is selected
                    release_selected = False
                    while(release_selected == False):
                        nx.press_buttons(controller_index, [nxbt.Buttons.DPAD_DOWN], up=1.2)
                        img = get_image()[317:343, 463:477]
                        img_mse = mse(release_select_check, img)
                        if img_mse < 50:
                            release_selected = True
                            break

                    # press A until the arrow isn't seen anymore
                    while(release_selected == True):
                        nx.press_buttons(controller_index, [nxbt.Buttons.A], up=1.2)
                        img = get_image()[317:343, 463:477]
                        img_mse = mse(release_select_check, img)
                        if img_mse > 50:
                            release_selected = False
                            break

                    # move arrow until "Yes" confirmation is highlighted
                    confirmation_selected = False
                    while(confirmation_selected == False):
                        nx.press_buttons(controller_index, [nxbt.Buttons.DPAD_UP], up=1.2)
                        img = get_image()[316:343, 462:479]
                        img_mse = mse(release_confirmation_check, img)
                        if img_mse < 40:
                            confirmation_selected = False
                            break

                    # press A until white text box is gone
                    released = False
                    while(released == False):
                        nx.press_buttons(controller_index, [nxbt.Buttons.A],up=1.2)
                        img = get_image()[446:460, 452:471]
                        img_mse = mse(release_textbox_check, img)
                        if img_mse > 10:
                            released = True
                            break
                    pokemon_at_0_pos = get_image()[124:132, 205:213] # update view
    return

def masuda(numBoxes):
    stats = None
    if os.path.isfile("stats.json"):
        with open("stats.json", "r") as f:
            stats = json.load(f)
    else:
        stats = {
            "eggs": 0,
            "issues": 0,
            "log": []
        }

    menu_open_check = np.array(Image.open("./check-imgs/menu_open.png"))
    pokemon_menu_check = np.array(Image.open("./check-imgs/pokemon_menu_check.png"))
    box_view_check = np.array(Image.open("./check-imgs/box_view_check.png"))
    multiselect_check = np.array(Image.open("./check-imgs/multiselect_ref.png"))
    bike_check = np.array(Image.open("./check-imgs/bike-ref.png"))
    oh_check = np.array(Image.open("./check-imgs/oh-ref.png"))
    egg_ref = np.array(Image.open("./check-imgs/egg_at_0_0_ref.png"))
    bookend_ref = np.array(Image.open("./check-imgs/bookend.png"))

    # Initialize an emulated controller and connect
    # to an available Switch.
    nx = nxbt.Nxbt()
    controller_index = nx.create_controller(
        nxbt.PRO_CONTROLLER,
        reconnect_address=nx.get_switch_addresses())
    nx.wait_for_connection(controller_index)

    add_to_stat_log(stats, "Controller Connected")

    time.sleep(5)

#    release_boxes(nx, controller_index)
#    get_new_eggs(528, nx, controller_index, stats)
#    move_to_bike_path(nx, controller_index)

    #first_page(nx, controller_index)
    #last_page(nx, controller_index)
#    return

    for currentBox in range(numBoxes):
        for currentCol in range(6):
            # starting position: off bike, on path, eggs in party, first col empty

            # Hop on the bike by first ensuring the registered menu is open and then checking to see if it has been closed (ie by pressing +)
            bike_view = False
            while (bike_view == False):
                img = get_image()[287:350, 330:393]
                nx.press_buttons(controller_index, [nxbt.Buttons.PLUS], up=2.0)
                img_mse = mse(bike_check, img)
                add_to_stat_log(stats, f"Bike check MSE: {img_mse}")
                if img_mse < 10:
                    print("Bike menu opened")
                    bike_view = True
                    break

            while (bike_view == True):
                img = get_image()[287:350, 330:393]
                nx.press_buttons(controller_index, [nxbt.Buttons.DPAD_DOWN], up=1.0)
                img_mse = mse(bike_check, img)
                add_to_stat_log(stats, f"Bike check MSE: {img_mse}")
                if img_mse > 50:
                    bike_view = False
                    break

            # On bike, now let's bike up and down until "Oh?" pops up
            ready_to_hatch = False
            while (ready_to_hatch == False):
                nx.press_buttons(controller_index, [nxbt.Buttons.DPAD_UP], down=11.0)
                nx.press_buttons(controller_index, [nxbt.Buttons.DPAD_DOWN], down=11.0)
                img = get_image()[398:425, 162:201]
                img_mse = mse(oh_check, img)
                print(str(img_mse))
                if img_mse < 20:
                    ready_to_hatch = True
                    break


            # press A until "Oh?" passes by 5 times
            # 40 x 28
            #img = get_image()[398:425, 162:201]

            # mash A 110 times to hatch
            for i in range(110):
                nx.press_buttons(controller_index, [nxbt.Buttons.A], up=1.0)

            # Get off bike by first ensuring the registered menu is open and then checking to see if it has been closed (ie by pressing DPAD_DOWN)
            bike_view = False
            while (bike_view == False):
                img = get_image()[287:350, 330:393]
                nx.press_buttons(controller_index, [nxbt.Buttons.PLUS], up=2.0)
                img_mse = mse(bike_check, img)
                add_to_stat_log(stats, f"Bike check MSE: {img_mse}")
                if img_mse < 10:
                    print("Bike menu opened")
                    bike_view = True
                    break

            while (bike_view == True):
                img = get_image()[287:350, 330:393]
                nx.press_buttons(controller_index, [nxbt.Buttons.DPAD_DOWN], up=1.0)
                img_mse = mse(bike_check, img)
                add_to_stat_log(stats, f"Bike check MSE: {img_mse}")
                if img_mse > 50:
                    bike_view = False
                    break

            # press X until in menu 
            menu_view = False
            while (menu_view == False):
                nx.press_buttons(controller_index, [nxbt.Buttons.X], up=1.0)
                img = get_image()
                img_mse = mse(menu_open_check, img)
                add_to_stat_log(stats, f"Menu check MSE: {img_mse}")
                if img_mse < 51:
                    menu_view = True
                    break

            # press A until in pokemon party
            pokemon_view = False
            while (pokemon_view == False):
                nx.press_buttons(controller_index, [nxbt.Buttons.A], up=1.0)
                img = relative_crop(get_image(), .975, 1.0, .025, 0.0)
                img_mse = mse(pokemon_menu_check, img)
                add_to_stat_log(stats, f"Pokemon view check MSE: {img_mse}")
                if img_mse < 50:
                    pokemon_view = True
                    break

            # press R until in box
            box_view = False
            while (box_view == False):
                nx.press_buttons(controller_index, [nxbt.Buttons.R], up=1.0)
                img = get_image()[38:56, 0:18, :]
                img_mse = mse(box_view_check, img)
                add_to_stat_log(stats, f"Box view check MSE: {img_mse}")
                if img_mse < 50:
                    box_view = True
                    break

            # press Y until multiselect is enabled
            multiselect = False
            while (multiselect == False):
                nx.press_buttons(controller_index, [nxbt.Buttons.Y], up=1.0)
                img = get_image()[0:28, 115:143, :]
                img_mse = mse(multiselect_check, img)
                add_to_stat_log(stats, f"Multiselect check MSE: {img_mse}")
                if img_mse < 50:
                    box_view = True
                    break

            # Move to first pokemon in party
            move_to((-1,1), nx, controller_index)

            # Select first pokemon
            while(is_selected((-1, 1)) == False):
                nx.press_buttons(controller_index, [nxbt.Buttons.A], up=2.0)

            # Select party
            while(is_selected((-1, 5)) == False):
                move_to((-1,5), nx, controller_index)

            # Pick up party
            while(get_picked_up_coords() == False):
                nx.press_buttons(controller_index, [nxbt.Buttons.A], up=2.0)

            # Move to open col (currentCol)
            move_to((currentCol,0), nx, controller_index, picked_up=True)
            
            # Place
            while(get_picked_up_coords() != False):
                nx.press_buttons(controller_index, [nxbt.Buttons.A], up=2.0)
            
            if(currentCol + 1 < 5): # ensuring we stay within this box

                # Move to next col (currentCol+1)
                move_to((currentCol+1,0), nx, controller_index)

                # Select first pokemon
                while(is_selected((currentCol+1, 0)) == False):
                    nx.press_buttons(controller_index, [nxbt.Buttons.A], up=2.0)

                # Select new pokemon
                while(is_selected((currentCol+1, 4)) == False):
                    move_to((currentCol+1,4), nx, controller_index)

                # Pick up new pokemon
                while(get_picked_up_coords() == False):
                    nx.press_buttons(controller_index, [nxbt.Buttons.A], up=2.0)

            else:

                # press R until we either see an egg or the bookmark pokemon
                pokemon_at_0_pos = get_image()[124:132, 205:213]
                indicator_found = False
                while(indicator_found == False):
                    nx.press_buttons(controller_index, [nxbt.Buttons.R], up=2.0)
                    pokemon_at_0_pos = get_image()[124:132, 205:213]

                    # if we see an egg, pick up (0,0)-(0,4)
                    if (mse(pokemon_at_0_pos, egg_ref) < 20):

                        indicator_found = True

                        # Move to (0,0)
                        move_to((0,0), nx, controller_index)

                        # Select first pokemon
                        while(is_selected((0, 0)) == False):
                            nx.press_buttons(controller_index, [nxbt.Buttons.A], up=2.0)

                        # Select new pokemon
                        while(is_selected((0,0)) == False):
                            move_to((currentCol+1,4), nx, controller_index)

                        # Pick up new pokemon
                        while(get_picked_up_coords() == False):
                            nx.press_buttons(controller_index, [nxbt.Buttons.A], up=2.0)
                    
                    # if we see a bookend, exit
                    if (mse(pokemon_at_0_pos, bookend_ref) < 20):
                        return



            # here on out it doesn't matter where we are, we can still just place in party

            # Move to party
            move_to((-1, 1), nx, controller_index, picked_up=True)
            
            # Place
            while(get_picked_up_coords() != False):
                nx.press_buttons(controller_index, [nxbt.Buttons.A], up=2.0)

            # press B until in menu view, and then B until out of menu view
            menu_view = False
            while (menu_view == False):
                nx.press_buttons(controller_index, [nxbt.Buttons.B], up=1.0)
                img = get_image()
                img_mse = mse(menu_open_check, img)
                add_to_stat_log(stats, f"Menu check MSE: {img_mse}")
                if img_mse < 60:
                    menu_view = True
                    break

            while (menu_view == True):
                nx.press_buttons(controller_index, [nxbt.Buttons.B], up=1.0)
                img = get_image()
                img_mse = mse(menu_open_check, img)
                add_to_stat_log(stats, f"Menu check MSE: {img_mse}")
                if img_mse > 60:
                    menu_view = False
                    break

if __name__ == "__main__":
    masuda(1)
#    init_bookends()
#    init_breed_species()
# 32x32
#    save_array_as_image(get_image()[124:132, 205:213], "egg_ref")
#                okemon_at_0_pos = get_image()[124:132, 205:213]
   #20x15
    #150x20
#    save_array_as_image(get_image()[365:384, 160:309], "man_talking_check")
#    print(get_picked_up_coords())
#    get_picked_up_coords(debug=True)
#    print("Done")
    send_message("Completed")

