from .core import *

# this is a list of keys to deactivate with a list of modes to deactivate them in
keymodes = [  # key    any   shift  ctrl   alt   oskey               modes

    ['V', False, False, False, True, False, ['Object Non-modal', 'Sculpt', 'Vertex Paint', 'Weight Paint', 'Image Paint']],

]


def opposingkeys(activation):
    wm = bpy.context.window_manager

    # deactivate the opposing keys to prevent clashing and reactivate them on unregister
    # keymode is a list containing the mode and key you want changed
    for key in keymodes:
        # mode is the mode you want the key to be (de)activated for.
        for mode in key[6]:
            km = wm.keyconfigs.active.keymaps[mode]

            # this iterates through all the keys in the current
            # hotkey layout and (de)activates the ones that
            # match the key we want to (de)activate
            for kmi in km.keymap_items:
                #print(kmi.type, "shift={0}".format(kmi.shift), "ctrl={0}".format(kmi.ctrl), "alt={0}".format(kmi.alt))
                if kmi.type == key[0] and kmi.any == key[1] \
                        and kmi.shift == key[2] and kmi.ctrl == key[3] \
                        and kmi.alt == key[4] and kmi.oskey == key[5]:

                    # (de)activate the current key
                    kmi.active = activation
