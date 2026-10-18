"""Flag staffs and flag mounts for the hull scripts (owner, October 17: sloop 2 flag positions, brigantine 3, Cavalier 4,
all empty at first; a crafted flag is plain clean white; flags install, remove and swap, flutter in the wind, and fray
and tear only from combat damage; destroyed fabric disappears while its pole remains).

DECIDED (delegated; recorded in Docs/OPEN_QUESTIONS_2026-10-15.md): a flag flies at the head of each mast, from a short
flagstaff above the masthead cap, and one ensign at the stern on an ensign staff. That is the owner's count exactly for
the sloop (one mast), the brigantine (two) and the Cavalier (three). The schooner was not named: she flies from her fore
and main mastheads and the stern, 3 (her mizzen flies none), so the count grows with the ship. The staffs are part of
the hull, so a destroyed flag's pole remains. A masthead is far out of reach: each flag's halyard comes down to a
belaying pin beside its mast (or the ensign staff's foot) at chest height, and that is where a survivor hoists or lowers
it. Sizes are tuning.
"""
import unreal

FLAG_STAFF = 260.0     # a masthead flagstaff's height above the cap, cm
ENSIGN_STAFF = 420.0   # the ensign staff's height above its deck
HALYARD_Y = 75.0       # a masthead halyard belays this far to starboard of its mast (clear of the sail mount)
HALYARD_Z = 110.0      # belaying pins stand this high above their deck
MASTHEAD_FLAG = 1.0    # flag scale (the flag is 150 x 100 cm at 1)
ENSIGN_FLAG = 1.25


def _truck(b, at):
    b.box((at[0], at[1], at[2] + 5), (9.0, 9.0, 10.0))


def masthead_staff(b, x, top, deck_z, mast_radius=15.0):
    """A flagstaff above the masthead cap at (x, 0, top), its truck, and its halyard down to a pin beside the mast.
    Returns (belay, hoist): where the halyard belays and where the flag's head flies, both in the hull's space."""
    foot, head = top + 12.0, top + 12.0 + FLAG_STAFF
    b.tube([(x, 0.0, foot - 20), (x, 0.0, head)], lambda k: (4.0, 2.6)[k], sides=8)
    _truck(b, (x, 0.0, head))
    belay = (x, HALYARD_Y, deck_z + HALYARD_Z)
    b.tube([(x, 4.0, head - 6), (x, mast_radius + 3.0, top - 40), (x, mast_radius + 3.0, deck_z + 400), belay], 0.8, sides=5)
    b.box(belay, (5.0, 5.0, 16.0))        # the pin the halyard is made fast to
    return belay, (x, 0.0, head - 14.0)


def ensign_staff(b, x, y, deck_z):
    """The ensign staff at the stern, raked a little aft, with its halyard made fast at its foot. Returns (belay, hoist)."""
    top = (x - 30.0, y, deck_z + ENSIGN_STAFF)
    b.tube([(x, y, deck_z - 5), top], lambda k: (5.5, 3.2)[k], sides=8)
    _truck(b, top)
    belay = (x + 12.0, y, deck_z + HALYARD_Z)
    b.tube([(top[0] + 4, y, top[2] - 6), belay], 0.8, sides=5)
    b.box(belay, (5.0, 5.0, 16.0))
    return belay, (top[0], y, top[2] - 14.0)


def flag_mount(mount_id, belay, hoist, scale):
    """A flag mount at its halyard's pin, flying its flag at the staff's head (FittedMeshTransform, relative to the pin)."""
    m = unreal.EWShipMount()
    m.set_editor_property('mount_id', mount_id)
    m.set_editor_property('type', unreal.EWShipMountType.FLAG)
    m.set_editor_property('transform', unreal.Transform(location=unreal.Vector(*belay)))
    m.set_editor_property('fitted_mesh_transform', unreal.Transform(
        location=unreal.Vector(hoist[0] - belay[0], hoist[1] - belay[1], hoist[2] - belay[2]), scale=unreal.Vector(scale, scale, scale)))
    return m
