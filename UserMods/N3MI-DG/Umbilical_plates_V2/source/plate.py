import cadquery as cq
import math
from cq_warehouse.thread import IsoThread

from config import profiles, frames, th_board_offset
from led_points import flipped, flipped_u, flipped_passive_h, flipped_passive_hu, flipped_passive_v, flipped_passive_vu
from plate_sketches import (
    tpu_sk, tpu_sk_inner, tpu_sk_clear, tpu_sk_clear2, tpu_sk_clear3, 
    thread_sk, thread_sk_inner, thread_sk_clear, thread_sk_clear2, thread_sk_clear3
)


def makeBodies(printer="voron", logo=True, panel_thick=4):
    extrusion_size        = profiles[printer]['extrusion_size']
    panel_cutout          = profiles[printer]['panel_cutout']
    panel_cutout          = profiles[printer]['panel_cutout']
    outer_thick           = profiles[printer]['outer_thick']
    outer_panel_z_offset  = profiles[printer]['outer_panel_z_offset']
    outer_panel_overlap_x = profiles[printer]['outer_panel_overlap_x']
    outer_panel_overlap_z = profiles[printer]['outer_panel_overlap_z']
    inner_panel_overlap_x = profiles[printer]['inner_panel_overlap_x']
    inner_panel_overlap_z = profiles[printer]['inner_panel_overlap_z']
    inner_thick           = profiles[printer]['inner_thick']
    panel_fillet          = profiles[printer]['panel_fillet']
    hex_size              = profiles[printer]['hex_size']
    hex_gap               = profiles[printer]['hex_gap']
    hex_filletl           = profiles[printer]['hex_filletl']
    hex_fillets           = profiles[printer]['hex_fillets']
    hex_depth             = profiles[printer]['hex_depth']
    hex_xz1               = profiles[printer]['hex_xz1']
    hex_xz2               = profiles[printer]['hex_xz2']
    ext_mount_offset      = profiles[printer]['ext_mount_offset']
    ext_hole_size         = profiles[printer]['ext_hole_size']
    face_hole_size        = profiles[printer]['face_hole_size']
    face_hole_z_offsets   = profiles[printer]['face_hole_z_offsets']
    face_thread_insert    = profiles[printer]['face_thread_insert']
    port_z_offset         = profiles[printer]['port_z_offset']
    
    tol                   = 0.2
    hex_r1                = (hex_size/2)*math.cos(math.pi/6)
    hex_off1              = (hex_r1*4+hex_gap, 0, 0)
    hex_off2              = (math.cos(60*math.pi/180)*(hex_r1*4+hex_gap), 0, math.sin(60*math.pi/180)*(hex_r1*4+hex_gap))
    outer_width           = panel_cutout[0] + (outer_panel_overlap_x*2)
    outer_height          = panel_cutout[1] + outer_panel_z_offset + outer_panel_overlap_z
    outer_hole_offset     = outer_width - (outer_panel_overlap_x*2) - ext_mount_offset
    ext_hole_cbore_len    = math.sqrt(((ext_hole_size[1]/2)*(ext_hole_size[1]/2))-((ext_hole_size[0]/2)*(ext_hole_size[0]/2))) * 2
    small_hole_cbore_len  = math.sqrt(((face_hole_size[1]/2)*(face_hole_size[1]/2))-((face_hole_size[0]/2)*(face_hole_size[0]/2))) * 2
    inner_width           = panel_cutout[0] + (inner_panel_overlap_x*2)
    inner_height          = (outer_height-extrusion_size-outer_panel_overlap_z) + inner_panel_overlap_z

    hex_offsets = [
        (hex_xz1[0],                         outer_thick,             hex_xz1[1]),
        (hex_xz1[0]+(-hex_off1[0]),          outer_thick+hex_off1[1], hex_xz1[1]+hex_off1[2]),
        (hex_xz1[0]+hex_off2[0],             outer_thick+hex_off2[1], hex_xz1[1]+hex_off2[2]),
        (hex_xz1[0]+hex_off2[0],             outer_thick+hex_off2[1], hex_xz1[1]+(-hex_off2[2])),
        (hex_xz1[0]+hex_off2[0]+hex_off1[0], outer_thick+hex_off2[1], hex_xz1[1]+(-hex_off2[2])),

        (hex_xz2[0],                outer_thick,             hex_xz2[1]),
        (hex_xz2[0]+(-hex_off2[0]), outer_thick+hex_off2[1], hex_xz2[1]+(-hex_off2[2]))
    ]

    if printer == "micron":
        passive_h = flipped_passive_hu
        passive_v = flipped_passive_vu
        leds      = flipped_u

    else: # Voron
        passive_h = flipped_passive_h
        passive_v = flipped_passive_v
        leds      = flipped

    # Create hex pattern
    hex_big   = cq.Workplane("XZ")
    hex_small = cq.Workplane("XZ")

    for offset in hex_offsets:
        hex_big = ( # To be cut from the outer plate
            hex_big.union(
                cq.Workplane("XZ")
                .placeSketch(
                    cq.Sketch()
                    .regularPolygon(hex_size, 6).vertices().fillet(hex_filletl),
                    cq.Sketch()
                    .regularPolygon(hex_size-hex_depth, 6).vertices().fillet(hex_fillets)
                    .moved(cq.Location(cq.Vector(0, 0, hex_depth)))
                )
                .loft()
                .translate(offset)
            )
        )

        hex_small = ( # Hex bodies
            hex_small
            .union(
                cq.Workplane("XZ")
                .placeSketch(
                    cq.Sketch()
                    .regularPolygon(hex_size-hex_depth, 6).vertices().fillet(hex_fillets)
                    .moved(cq.Location(cq.Vector(0, 0, hex_depth))),
                    cq.Sketch()
                    .regularPolygon(hex_size-hex_depth*2, 6).vertices().fillet(hex_fillets/2)
                    
                )
                .loft()
                .translate(offset)
            )
        )

    # Face mounting holes negative
    x_screw_offset = panel_cutout[0]/2 - panel_fillet/2

    face_mount = (
        cq.Workplane("XZ").transformed(offset=(0, 0, (panel_thick+0.5)))
        .pushPoints([ # Threaded insert
                (x_screw_offset,    face_hole_z_offsets[0]), 
                (-x_screw_offset, face_hole_z_offsets[0]), 
                (x_screw_offset,    face_hole_z_offsets[1]), 
                (-x_screw_offset, face_hole_z_offsets[1])
        ]).circle(face_thread_insert[0]/2).extrude(face_thread_insert[1])

        .faces(">Y").workplane()
        .pushPoints([ # Screw thread
            (x_screw_offset,    face_hole_z_offsets[0]), 
            (-x_screw_offset, face_hole_z_offsets[0]), 
            (x_screw_offset,    face_hole_z_offsets[1]), 
            (-x_screw_offset, face_hole_z_offsets[1])
        ]).circle(face_hole_size[0]/2).extrude(panel_thick+0.5+(outer_thick))
        
        .faces(">Y").workplane()
        .pushPoints([ # Screw head
            (x_screw_offset,    face_hole_z_offsets[0]), 
            (-x_screw_offset, face_hole_z_offsets[0]), 
            (x_screw_offset,    face_hole_z_offsets[1]), 
            (-x_screw_offset, face_hole_z_offsets[1])
        ]).circle(face_hole_size[1]/2).extrude(-face_hole_size[2])
        
        .faces(">Y").workplane()
        .pushPoints([ # Hole bridges 1
            (x_screw_offset,    face_hole_z_offsets[0]), 
            (-x_screw_offset, face_hole_z_offsets[0]), 
            (x_screw_offset,    face_hole_z_offsets[1]), 
            (-x_screw_offset, face_hole_z_offsets[1])
        ]).rect(small_hole_cbore_len, face_hole_size[0]).extrude(-(face_hole_size[2]+0.2))
        
        .faces(">Y").workplane()
        .pushPoints([ # Hole bridges 2
            (x_screw_offset,    face_hole_z_offsets[0]), 
            (-x_screw_offset, face_hole_z_offsets[0]), 
            (x_screw_offset,    face_hole_z_offsets[1]), 
            (-x_screw_offset, face_hole_z_offsets[1])
        ]).rect(face_hole_size[0], face_hole_size[0]).extrude(-(face_hole_size[2]+0.4))
    )

    # Outer plate blank
    outer_plate = (
        # Main body
        cq.Workplane("XZ")
        .rect(outer_width, outer_height).extrude(-(outer_thick))

        # Remove panel section
        .faces("<Y").workplane(centerOption="CenterOfBoundBox").pushPoints([
            (0, outer_height/2-outer_panel_z_offset/2+tol/2)
        ]).rect(outer_width, outer_panel_z_offset-tol).extrude(panel_thick-tol)

        # Reinforce panel opening
        .faces(">Y").workplane(centerOption="CenterOfBoundBox").pushPoints([
            (0, -((outer_height/2)-panel_cutout[1]/2-outer_panel_overlap_z-tol))
        ]).rect(panel_cutout[0]-tol, panel_cutout[1]).extrude(-(outer_thick+panel_thick+0.5))

        # Add clearance for extrusion
        .faces(">Y").workplane(centerOption="CenterOfBoundBox", offset=-(outer_thick+panel_thick)+tol)
        .pushPoints([(0, outer_height/2-extrusion_size/2)])
        .rect(panel_cutout[0]+outer_panel_overlap_x*2, extrusion_size+tol*2).extrude(-1, "cut")


        # Add the panel fillet
        .faces("<Z[-2]").edges("|Y").fillet(panel_fillet-tol)

        # Extrusion mount holes
        .faces(">Y").workplane(centerOption="CenterOfBoundBox")
        .pushPoints([ # Counterbored hole
            (outer_hole_offset/2, outer_height/2-extrusion_size/2), 
            (-outer_hole_offset/2, outer_height/2-extrusion_size/2)
        ]).cboreHole(ext_hole_size[0], ext_hole_size[1], ext_hole_size[2])
    
        .faces(">Y").workplane(centerOption="CenterOfBoundBox")
        .pushPoints([ # Hole bridges 1
            (outer_hole_offset/2, outer_height/2-extrusion_size/2), 
            (-outer_hole_offset/2, outer_height/2-extrusion_size/2)
        ]).rect(ext_hole_cbore_len, ext_hole_size[0]).extrude(-(ext_hole_size[2]+0.2), "cut")

        .faces(">Y").workplane(centerOption="CenterOfBoundBox")
        .pushPoints([ # Hole bridges 2
            (outer_hole_offset/2, outer_height/2-extrusion_size/2), 
            (-outer_hole_offset/2, outer_height/2-extrusion_size/2)
        ]).rect(ext_hole_size[0], ext_hole_size[0]).extrude(-(ext_hole_size[2]+0.4), "cut")

        # Styling
        .faces(">Z or <Z").edges("|Y").chamfer(7)
        .faces(">Y").edges(cq.NearestToPointSelector((outer_width/2, 0, outer_height/2))).chamfer(outer_thick-2)
        .faces(">Y").edges(cq.NearestToPointSelector((-outer_width/2, 0, outer_height/2))).chamfer(outer_thick-2)
        .faces(">Y").edges(cq.NearestToPointSelector((outer_width/2, 0, -outer_height/2))).chamfer(outer_thick-2)
        .faces(">Y").edges(cq.NearestToPointSelector((-outer_width/2, 0, -outer_height/2))).chamfer(outer_thick-2)
        .faces(">Y").edges("|X or |Z").chamfer(outer_thick-3)

        # Cut hexes
        .cut(hex_big)

        # Mounting holes for the face plate
        .cut(face_mount)
    )

    # Inner plate blank
    face_plate = (
        # Main body
        cq.Workplane("XZ")
        .rect(inner_width, inner_height).extrude(inner_thick)


    
        # Styling
        .faces(">X or <X").edges("<Z").chamfer(7, inner_height/2)
        .faces("<Z").edges("|Y").chamfer(5)
        .faces("<X or >X").edges("<Y").chamfer(inner_thick-2)
        .faces(cq.NearestToPointSelector((-inner_width/2, -1, -inner_height/2+10))).edges("<Y").chamfer(inner_thick-2)
        .faces(cq.NearestToPointSelector((-inner_width/2, -1, -inner_height/2))).edges("<Y").chamfer(inner_thick-2)
        .faces(cq.NearestToPointSelector((inner_width/2, -1, -inner_height/2+10))).edges("<Y").chamfer(inner_thick-2)
        .faces(cq.NearestToPointSelector((inner_width/2, -1, -inner_height/2))).edges("<Y").chamfer(inner_thick-2)
        .faces("<Y").edges("<Z or >Z").chamfer(0.4)
        
        # Move to correct position
        .translate((0, -(panel_thick-tol), outer_height/2-extrusion_size-inner_height/2-tol))

        # Add panel insert clearance
        .cut(
            cq.Workplane("XZ")
            .rect(panel_cutout[0], panel_cutout[1])
            .extrude(panel_thick+0.5)
            .faces("<Z").edges("<X or >X").fillet(panel_fillet)
            .translate((0, 0, outer_height/2-panel_cutout[1]/2-outer_panel_z_offset))
        )

        # Remove extra thickness to aid in flex
        .faces(">Z[-2]").workplane(centerOption="CenterOfBoundBox")
        .pushPoints([
            (0, (-inner_thick/2+0.5+tol/2)+2.6)
        ]).rect(panel_cutout[0]-(panel_fillet*2), inner_thick).extrude(inner_height, "cut")

        # Mounting holes
        .cut(face_mount)

    )

    # Add Logo
    if logo:
        outer_plate = (
            outer_plate
            # LED holder
            .faces("<Y").workplane().pushPoints([(0, port_z_offset)]).polygon(6, 20.6+3.2, circumscribed=True).extrude(2.6-tol)
            .faces("<Y").workplane(centerOption="CenterOfBoundBox").pushPoints([(8.2+1.6, 0), (-(8.2+1.6), 0)]).polygon(6, 6.5+1.6, circumscribed=True).extrude(-(2.6-tol))
            .faces("<Y").workplane(centerOption="CenterOfBoundBox").pushPoints([(0, 11.15+1.6), (0, -(11.15+1.6))]).rect(10, 2.5).extrude(-(2.6-tol), "cut")

            .faces("<Y").workplane(centerOption="CenterOfBoundBox").polygon(6, 20.6, circumscribed=True).extrude(-1.6, "cut")
            .faces("<Y").workplane(centerOption="CenterOfBoundBox").pushPoints([(8.2, 0), (-8.2, 0)]).polygon(6, 6.5, circumscribed=True).extrude(-1.6, "cut")
            .faces("<Y").workplane(centerOption="CenterOfBoundBox").pushPoints([(0, 11.15-0.6), (0, -11.15+0.6)]).rect(8.5, 2.5-1.2).extrude(-(2.6-tol))
            .faces("<Y").workplane(centerOption="CenterOfBoundBox").pushPoints([(0, 11.15-0.6+1.2), (0, -11.15+0.6-1.2)]).rect(10, 2.5-1.2).extrude(-(2.6-tol), "cut")

            # LED wire hole
            .cut(
                cq.Workplane("XZ")
                .polygon(6, 20.6-3.2, circumscribed=True).extrude(outer_thick+panel_thick+inner_thick)
                .faces("<Y").workplane(centerOption="CenterOfBoundBox").pushPoints([(0, 11.15-1.6), (0, -(11.15-1.6))]).rect(10, 2.5).extrude(-(outer_thick+panel_thick+inner_thick), "cut")
                .translate((0, outer_thick+panel_thick, port_z_offset))
            )

            # LED flared opening
            .cut(
                cq.Workplane("XZ").transformed(offset=(0, port_z_offset, -(outer_thick)))
                .placeSketch(
                    cq.Sketch()
                    .regularPolygon(16 if printer == "voron" else 12, 6).vertices().fillet(3.2),
                    cq.Sketch()
                    .regularPolygon(10, 6).vertices().fillet(2)
                    .moved(cq.Location(cq.Vector(0, 0, outer_thick+panel_thick)))
                )
                .loft()
            )

        )

        # Diffuser clearance
        face_plate = (
            face_plate
            # Diffuser shape
            .faces(">Y[-3]").workplane(centerOption="CenterOfBoundBox").polygon(6, 20.6, circumscribed=True).extrude(-1.4, "cut")
            .faces(">Y[-3]").workplane(centerOption="CenterOfBoundBox").pushPoints([(8.2, 0), (-8.2, 0)]).polygon(6, 6.5, circumscribed=True).extrude(-1.4, "cut")
            .faces(">Y[-3]").workplane(centerOption="CenterOfBoundBox").pushPoints([(0, 11.15-0.25), (0, -11.15+0.25)]).rect(10, 2.5-0.5).extrude(-2)

            # Holding tab holes
            .faces(cq.NearestToPointSelector((5, -(outer_thick+panel_thick), outer_panel_overlap_z/4-port_z_offset))).workplane(centerOption="CenterOfBoundBox").pushPoints([(0.2, 0.0)]).rect(1, 4).extrude(-0.6, "cut")
            .faces(cq.NearestToPointSelector((-5, -(outer_thick+panel_thick), outer_panel_overlap_z/4-port_z_offset))).workplane(centerOption="CenterOfBoundBox").pushPoints([(-0.2, 0.0)]).rect(1, 4).extrude(-0.6, "cut")
            
            # # # Pressure points
            .faces(cq.NearestToPointSelector((0, -(outer_thick+panel_thick), -12))).workplane(centerOption="CenterOfBoundBox").pushPoints([(2.5, 0), (-2.5, 0)]).rect(1.2, 1.4).extrude(0.4)
        )

        # Add the logo
        face_center = face_plate.faces(cq.NearestToPointSelector((0, -(outer_thick+panel_thick), port_z_offset))).objects[0].BoundingBox().center.z

        face_plate = face_plate.cut(
            cq.importers.importDXF(
                "../supplements/logo.dxf", 
                include=[f"{printer}_cut"]
            ).wires().toPending().extrude(-(outer_thick+panel_thick+inner_thick))
            .rotate((0, 0, 0), (1, 0, 0), -90)
            .translate((0, 0, face_center))
        )

        # Create Logo Insert
        logo_insert = (
            cq.Workplane()
            .polygon(6, 20.5, circumscribed=True).extrude(-1.4)
            .faces(">Z").workplane().pushPoints([(8.2, 0), (-8.2, 0)]).polygon(6, 6, circumscribed=True).extrude(-1.4)

            .faces("<Z").workplane(centerOption="CenterOfBoundBox").pushPoints(leds).rect(2, 2).extrude(-1, "cut")
            .faces("<Z").workplane(centerOption="CenterOfBoundBox").pushPoints(passive_h).rect(2, 1).extrude(-0.8, "cut")
            .faces("<Z").workplane(centerOption="CenterOfBoundBox").pushPoints(passive_v).rect(1, 2).extrude(-0.8, "cut")

            .faces("<Z").workplane().pushPoints([(0, 11.25), (0, -11.25)]).rect(10, 3).extrude(-4, "cut")
        )

        face_len = logo_insert.faces("<Y").edges("<Z").objects[0].Length()

        logo_insert = (
            logo_insert
            .faces("<Y").workplane(centerOption="CenterOfBoundBox").rect(face_len, 1.4).extrude(-0.8)
            .faces(">Y").workplane(centerOption="CenterOfBoundBox").rect(face_len, 1.4).extrude(-0.8)

            .union(
                cq.importers.importDXF("../supplements/logo.dxf", include=[f"{printer}_emboss"]).wires().toPending().extrude(0.5)
                .rotate((0, 0, 0), (1, 0, 0), 180)
                .translate((0, 0, 0.5))
                .faces(">Z").chamfer(0.3)
            )

            .faces(cq.NearestToPointSelector((10, 10, -2))).workplane(centerOption="CenterOfBoundBox").pushPoints([(0, 0.3)]).rect(3.5, 0.8).extrude(0.3)
            .faces(cq.NearestToPointSelector((10, 12, -2))).edges("|Z").chamfer(0.299)
            .faces(cq.NearestToPointSelector((-10, 10, -2))).workplane(centerOption="CenterOfBoundBox").pushPoints([(0, 0.3)]).rect(3.5, 0.8).extrude(0.3)
            .faces(cq.NearestToPointSelector((-10, 12, -2))).edges("|Z").chamfer(0.299)

            .rotate((0, 0, 0), (1, 0, 0), 90)
            .translate((0, -(panel_thick-tol+inner_thick-1.4), face_center))
        )

    else:
        logo_insert = None

    return(outer_plate, face_plate, logo_insert, hex_small)


def makePG7Thread():
    thread = IsoThread(major_diameter=12.65, pitch=1.27, length=30)
    core = (
        cq.Workplane()
        .circle(thread.root_radius)
        .extrude(100)
        .translate((0, 0, -(100-thread.length)))
    )

    return(thread.cq_object.fuse(core.val()).translate((0, 0, 3)))


def makePlate(outer_plate, face_plate, printer="voron", printer_size=300, tool_count=6, dock_width=60, panel_thick=4, logo=True, port_pos="split", port_type="TPU", thread_negative=None, mount_rail="TOP"):
    extrusion_size = profiles[printer]['extrusion_size']
    inner_thick    = profiles[printer]['inner_thick']
    outer_thick    = profiles[printer]['outer_thick']
    port_length    = profiles[printer]['port_length']
    port_angle     = profiles[printer]['port_angle'] if port_type == "TPU" else 66
    port_z_offset  = profiles[printer]['port_z_offset'] if port_type == "TPU" else -8
    frame_deadzone = profiles[printer]['frame_deadzone']
    back_centers   = profiles[printer]['back_centers_logo' if logo else 'back_centers']
    frame_x_width  = frames[printer_size][0]
    port_y_rotate  = 180 if mount_rail == "BOTTOM" else 0
    screw_point_angle_left, screw_point_angle_right = (-45, 45) if mount_rail == "BOTTOM" else (45, -45)

    logo_tools = [i for i in range(1, tool_count+1) if i <= frames[printer_size][2 if dock_width == 60 else 3]/2 or i % 2 == 0]
    center_offset  = profiles[printer]['center_offset'] if logo and tool_count in logo_tools else 0

    if printer == "voron" and tool_count == 2:
         center_offset += 10

    sk        = globals()[f"{'tpu' if port_type == 'TPU' else 'thread'}_sk"]
    sk_inner  = globals()[f"{'tpu' if port_type == 'TPU' else 'thread'}_sk_inner"]
    sk_clear  = globals()[f"{'tpu' if port_type == 'TPU' else 'thread'}_sk_clear"]
    sk_clear2 = globals()[f"{'tpu' if port_type == 'TPU' else 'thread'}_sk_clear2"]
    sk_clear3 = globals()[f"{'tpu' if port_type == 'TPU' else 'thread'}_sk_clear3"]

    back_offsets = []

    # Work out the centers between docks
    if port_pos == "split":
        tc = tool_count - 1
        dc = (frame_x_width-(frame_deadzone*2)-dock_width) / (tc)
    
    else:
        tc = (tool_count*2) - 1
        dc = dock_width
    
    # Umbilical plate and dock offsets per tool count
    bc = back_centers[tool_count]
    co = center_offset

    port_vars = {
        1: [
            {"back_offset": 0,"dock_offset": 0}
        ],
        2: [
            {"back_offset": -(bc/2+co/2), "dock_offset": -dc/2},
            {"back_offset": bc/2+co/2,    "dock_offset": dc/2}
        ],
        3: [
            {"back_offset": -(bc+co/2), "dock_offset": -dc},
            {"back_offset": 0,          "dock_offset": 0},
            {"back_offset":  bc+co/2,   "dock_offset": dc},
        ],
        4: [
            {"back_offset": -(bc*1.5+co/2), "dock_offset": -dc*1.5},
            {"back_offset": -(bc/2+co/2),   "dock_offset": -dc/2},
            {"back_offset": bc/2+co/2,      "dock_offset": dc/2},
            {"back_offset": bc*1.5+co/2,    "dock_offset": dc*1.5},

        ],
        5: [
            {"back_offset": -(bc*2+co/2), "dock_offset": -dc*2},
            {"back_offset": -(bc+co/2),   "dock_offset": -dc},
            {"back_offset": 0,            "dock_offset": 0},
            {"back_offset":  bc+co/2,     "dock_offset": dc},
            {"back_offset": (bc*2+co/2),  "dock_offset": dc*2},

        ],
        6: [
            {"back_offset": -(bc*2.5+co/2), "dock_offset": -((dc/2)+(dc*2))},
            {"back_offset": -(bc*1.5+co/2), "dock_offset": -((dc/2)+dc)},
            {"back_offset": -(bc/2+co/2),   "dock_offset": -dc/2},
            {"back_offset":  bc/2+co/2,     "dock_offset": dc/2},
            {"back_offset": (bc*1.5+co/2),  "dock_offset": (dc/2)+dc},
            {"back_offset": (bc*2.5+co/2),  "dock_offset": (dc/2)+(dc*2)},
        ],
        7: [
            {"back_offset": -((bc*3)+co/2), "dock_offset": -dc*3},
            {"back_offset": -(bc*2+co/2),   "dock_offset": -dc*2},
            {"back_offset": -(bc+co/2),     "dock_offset": -dc},
            {"back_offset": 0,              "dock_offset": 0},               
            {"back_offset":  bc+co/2,       "dock_offset":  dc},
            {"back_offset": (bc*2+co/2),    "dock_offset": dc*2},
            {"back_offset": (bc*3+co/2),    "dock_offset": dc*3},
        ]
    }

    # Create the port body
    if port_type == "TPU":
        port_shape = (
            cq.Workplane().placeSketch(sk).extrude(port_length*4).translate((0, 0, -port_length*3))
            .faces(">Z").workplane().placeSketch(sk_inner).cutBlind(-port_length*4)
            .faces(">Z").edges().item(0).fillet(1)
            .faces(">Z").edges().item(6).chamfer(0.2, 2)
        )

    else:
        port_shape = (
            cq.Workplane().placeSketch(sk).extrude(port_length*4).translate((0, 0, -port_length*3))
            .faces(">Z").edges().item(0).fillet(0.5)
            .cut(thread_negative)
        )

    dock_positions = []

    for tool in range(tool_count):
        if port_pos == "left" and tool_count < 4:
            back_offset = port_vars[tool_count*2][tool]['back_offset']
            dock_offset = -((frame_x_width/2-frame_deadzone-dock_width/2)-(dock_width*tool))

        elif port_pos == "right" and tool_count < 4:
            back_offset = -port_vars[tool_count*2][tool]['back_offset']
            dock_offset = (frame_x_width/2-frame_deadzone-dock_width/2)-(dock_width*tool)
        else:
            back_offset = port_vars[tool_count][tool]['back_offset']
            dock_offset = port_vars[tool_count][tool]['dock_offset']

        dock_angle  = math.atan((dock_offset-back_offset)/(frames[printer_size][1] + extrusion_size - th_board_offset)) * 180 / math.pi

        if dock_width == 60:
            dock_position = (
                dock_offset, 
                -frames[printer_size][1]-frames[printer_size][4]-panel_thick+5, 
                -50
            )
        
        else:
            dock_position = (
                dock_offset, 
                -frames[printer_size][1]-frames[printer_size][4]-panel_thick-5, 
                -50
            )


        dock_positions.append(dock_position)

        if port_pos == "split" and tool <= tool/2:
            dock_angle  = -abs(dock_angle)
            back_offset = -abs(back_offset)
        
        back_offsets.append(back_offset)

        # Select clearance type depending on the tools position
        if tool == 0 and port_pos != "right":
            clear = sk_clear3

        elif tool == tool_count-1 and port_pos != "left":
            clear = sk_clear2
    
        else:
            clear = sk_clear

        # Negative of the port opening
        locals()[f'inner_{tool}'] = (
            cq.Workplane().placeSketch(sk_inner).extrude(port_length*8).translate((0, 0, -port_length*4))
        )

        if port_type != "TPU":
            bowden = (
                cq.Workplane()
                .circle(2.3).extrude(port_length*2.75)
                .faces("<Z").workplane(centerOption="CenterOfBoundBox").circle(2.3).revolve(18.5, (0, port_length, 0), (-1, port_length, 0))
                .faces("<Z").workplane(centerOption="CenterOfBoundBox").circle(2.3).extrude(port_length*4)
                .translate((0, 11.2, port_length+1))
            )

            bowden = bowden.union(
                cq.Workplane()
                .circle(5.3).extrude(port_length*4)
                .translate((0, 3, -port_length*4))
                .faces(">Z").workplane(centerOption="CenterOfBoundBox").pushPoints([(0, -1.5)]).rect(10.6, 3).extrude(-port_length*4)
                .faces(">Z").chamfer(2.5)
            )

            screw_offsets = [1.0, 1.8, 2.5, 2.5, 1.8, 1.0]

            screw_point = (
                cq.Workplane("XZ")
                .circle(4.7/2)
                .extrude(5.63+4.5)
                .translate((0, 0, -(port_length+outer_thick-(screw_offsets[tool]))))
                .rotate((0, 0, 0), (0, 0, 1), screw_point_angle_left if dock_angle < 0 else screw_point_angle_right)
            )

            locals()[f'inner_{tool}'] = locals()[f'inner_{tool}'].union(bowden).union(screw_point)

        else:
            # Add notch for spring steel
            locals()[f'inner_{tool}'] = (
                locals()[f'inner_{tool}']
                .union(
                    cq.Workplane("YZ")
                    .polygon(6, 10, circumscribed=True).extrude(4.5)
                    .translate((-2.25, 2, port_length-6))
                )
            )

        locals()[f'inner_{tool}'] = (
            locals()[f'inner_{tool}']
            .rotate((0, 0, 0), (1, 0, 0), port_angle)
            .rotate((0, 0, 0), (0, 1, 0), port_y_rotate)
            .rotate((0, 0, 0), (0, 0, 1), dock_angle)
            .translate((back_offset, -(panel_thick+inner_thick), port_z_offset))
        )

        # Port moved and rotated into position
        locals()[f'body_{tool}'] = (
            port_shape
            .rotate((0, 0, 0), (1, 0, 0), port_angle)
            .rotate((0, 0, 0), (0, 1, 0), port_y_rotate)
            .rotate((0, 0, 0), (0, 0, 1), dock_angle)
            .translate((back_offset, -(panel_thick+inner_thick), port_z_offset))
            .cut(outer_plate.faces("<Y[-3]" if logo else "<Y").workplane().rect(printer_size, printer_size).extrude(-printer_size))
        )

        # Port clearance for the face plate. 
        locals()[f'clear_{tool}'] = (
            cq.Workplane()
            .transformed(offset=(0, 0, -port_length*1.7))
            .placeSketch(clear, sk_clear.moved(cq.Location(cq.Vector(0, 0, port_length*2.6))))
            .loft()
            .rotate((0, 0, 0), (1, 0, 0), port_angle)
            .rotate((0, 0, 0), (0, 1, 0), port_y_rotate)
            .rotate((0, 0, 0), (0, 0, 1), dock_angle)
            .translate((back_offset, -(panel_thick+inner_thick), port_z_offset))
        )

    for tool in range(tool_count):
        outer_plate = outer_plate.union(locals()[f'body_{tool}']) # Attach the ports
        face_plate  = face_plate.cut(locals()[f'clear_{tool}'])   # Add clearance to the face plate

    for tool in range(tool_count):
        outer_plate = outer_plate.cut(locals()[f'inner_{tool}'])  # Clear out the inside of the ports
    
    # Add some extra clearance to the face plate for larger tool counts
    if tool_count == 6 and logo or tool_count == 7:
        face_plate = (
            face_plate
            .faces(">Y[-2]").item(0).edges().item(4).chamfer(0.6)
            .faces(">Y[-2]").item(1).edges().item(4).chamfer(0.6)
        )

    return(outer_plate, face_plate, dock_positions)

 