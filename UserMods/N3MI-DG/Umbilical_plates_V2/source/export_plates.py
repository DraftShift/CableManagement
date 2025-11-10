import cadquery as cq
import os
import zipfile
import scour.scour as scour
import time

from plate import makeBodies, makePG7Thread, makePlate
from config import frames, docks, profiles

def makePath(p):
    if not os.path.exists(p):
        print("Creating directory", p)
        os.makedirs(p)


def validPlate(printer_size, tool_count, port_pos, dock_size, logo):
    max_tool_count = frames[printer_size][2 if dock_size == 60 else 3]

    if port_pos in ["left", "right"]:
        if tool_count <= max_tool_count/2 and logo:
            return(True)

        else:
            return(False)
        
    elif tool_count > max_tool_count:
        return(False)

    elif tool_count == 7 and port_pos == "split":
        return(False)
    
    elif logo and tool_count % 2 != 0:
        return(False)
    
    elif not logo and tool_count % 2 == 0:
        return(False)
    
    elif printer_size == 180 and tool_count == max_tool_count and port_pos == "center":
        return(False)

    # The following are valid but have no benefit.
    elif printer_size == 250 and dock_size == 60 and tool_count == 5 and port_pos == "center":
        return(False)

    elif printer_size == 250 and dock_size == 76 and tool_count == 4 and port_pos == "center":
        return(False)

    elif printer_size == 300 and dock_size == 76 and tool_count == 4 and port_pos == "center":
        return(False)

    elif printer_size == 300 and dock_size == 60 and tool_count == 6 and port_pos == "center":
        return(False)

    elif printer_size == 350 and dock_size == 60 and tool_count == 6 and port_pos == "center":
        return(False)

    elif printer_size == 350 and dock_size == 76 and tool_count == 5 and port_pos == "center":
        return(False)

    else:
        return(True)


def main():
    printers = [
            {"name": "voron", "sizes": [250, 300, 350], "dock_widths": [60, 76], "port_types": ["TPU", "THREAD"], "mount_rail": ["TOP", "BOTTOM"]},
            {"name": "micron", "sizes": [180], "dock_widths": [60], "port_types": ["TPU"], "mount_rail": ["TOP", "BOTTOM"]}
    ]

    type_count   = 0
    valid_plates = []
    panel_thick  = 4
    parent_path  = os.path.abspath(os.path.join(os.getcwd(), os.pardir))
    stl_path     = os.path.join(parent_path, "STL")
    img_path     = os.path.join(parent_path, "SVG")
    plate_path   = os.path.join(stl_path,    "Plates")
    
    makePath(stl_path)
    makePath(img_path)

    port_positions = ["left", "right", "center", "split"]

    for printer in printers:
        for size in printer['sizes']:
            locals()[f"{printer['name']}_{size}_assm"] = cq.Assembly(name=f"{size}mm_{printer['name']}_Plates")

    assm_xoffsets = {
        180: 0,
        250: 200,
        300: 400,
        350: 600
    }

    assm_zoffsets = {
        180: 0,
        250: 0,
        300: 0,
        350: 0
    }

    PG7_thread = makePG7Thread()
    makePath(plate_path)

    for printer in printers:
        printer_path = os.path.join(plate_path, printer['name'].title())
        makePath(printer_path)

        for logo in [False, True]:
            print("Generating", printer['name'].title(), "Blank Plate")
            outer_plate, face_plate, logo_insert, hexes = makeBodies(printer=printer['name'], logo=logo, panel_thick=panel_thick)

            for printer_size in printer['sizes']:
                size_path = os.path.join(printer_path, str(printer_size))
                max_tool_count = frames[printer_size][2]
                makePath(size_path)
                
                for tool_count in range(2, max_tool_count+1):
                    tool_count_path = os.path.join(size_path, f"{tool_count} Tools")
                    makePath(tool_count_path)

                    for dock in docks:
                        if dock['width'] in printer['dock_widths']:
                            max_tool_count = frames[printer_size][2 if dock['width'] == 60 else 3]

                            if tool_count <= max_tool_count:
                                dock_path = os.path.join(tool_count_path, f"{dock['width']}mm Wide Dock")
                                makePath(dock_path)

                                for port_type in printer['port_types']:
                                    port_name = port_type.title()+"ed" if port_type == "THREAD" else port_type
                                    port_path = os.path.join(dock_path, port_name)
                                    makePath(port_path)

                                    for port_pos in port_positions:
                                        if validPlate(printer_size, tool_count, port_pos, dock['width'], logo):
                                            position_path = os.path.join(port_path, port_pos.title())
                                            makePath(position_path)

                                            for mount_rail in printer['mount_rail']:

                                                name = f"{printer['name'].title()}_{printer_size}_{dock['width']}mm_{tool_count}tools_{port_pos}_{port_type}_{mount_rail}_rail"

                                                outer_name = f"{name}_Outer"
                                                face_name = f"{name}_Face"

                                                print("Calculating", name)
                                                type_count += 1
                                                print(type_count)

                                                if port_type == "TPU":
                                                    thread_negative = None
                                                else:
                                                    thread_negative = PG7_thread

                                                _outer_plate, _face_plate, dock_positions = makePlate(
                                                    outer_plate, 
                                                    face_plate, 
                                                    printer=printer['name'], 
                                                    printer_size=printer_size, 
                                                    tool_count=tool_count, 
                                                    dock_width=dock['width'],
                                                    logo=logo, 
                                                    port_pos=port_pos, 
                                                    port_type=port_type,
                                                    thread_negative=thread_negative,
                                                    mount_rail=mount_rail
                                                )

                                                # Export STL
                                                stl_outer_plate = _outer_plate.union(hexes).rotate((0, 0, 0), (1, 0, 0), -90)
                                                stl_face_plate   = _face_plate.rotate((0, 0, 0), (1, 0, 0), 90)

                                                print("Generating", f"{outer_name}.stl")
                                                cq.exporters.export(stl_outer_plate, os.path.join(position_path, f"{outer_name}.stl"), angularTolerance=0.3)

                                                print("Generating", f"{face_name}.stl")
                                                cq.exporters.export(stl_face_plate, os.path.join(position_path, f"{face_name}.stl"), angularTolerance=0.3)

                                                if logo:
                                                    logo_name = f"{printer['name'].title()}_Logo_Insert.stl"

                                                    print("Generating", logo_name)
                                                    cq.exporters.export(logo_insert.rotate((0, 0, 0), (-1, 0, 0), 90), os.path.join(position_path, logo_name))

                                                # Export CAD
                                                assm = cq.Assembly(name=f"_{name}")

                                                assm.add(
                                                    _face_plate.translate((assm_xoffsets[printer_size], 0, assm_zoffsets[printer_size])),
                                                    name=f"{name}_Face_Plate", 
                                                    color=cq.Color("darkorchid4")
                                                )

                                                assm.add(
                                                    _outer_plate.translate((assm_xoffsets[printer_size], 0, assm_zoffsets[printer_size])), 
                                                    name=f"{name}_Outer",      
                                                    color=cq.Color("gray18")
                                                
                                                )

                                                assm.add(
                                                    hexes.translate((assm_xoffsets[printer_size], 0, assm_zoffsets[printer_size])),
                                                    name=f"{name}_Hexes",
                                                    color=cq.Color("darkorchid4")
                                                )

                                                if logo:
                                                    assm.add(
                                                        logo_insert.translate((assm_xoffsets[printer_size], 0, assm_zoffsets[printer_size])), 
                                                        name=f"{printer['name'].title()} Insert", 
                                                        color=cq.Color("GhostWhite")
                                                    )
                                                
                                                locals()[f"{printer['name']}_{printer_size}_assm"].add(assm, name=name)

                                                assm_zoffsets[printer_size] += 100

                                                # Assembly for image
                                                frame = (
                                                    cq.Workplane()
                                                    .box(frames[printer_size][0]+(frames[printer_size][4]*2), frames[printer_size][1]+(frames[printer_size][4]*2), frames[printer_size][4])
                                                    .faces(">Z").workplane().rect(frames[printer_size][0], frames[printer_size][1]).extrude(-frames[printer_size][4], "cut")
                                                    
                                                    .translate((
                                                        0, 
                                                        -frames[printer_size][1]/2-frames[printer_size][4]-panel_thick, 
                                                        (profiles[printer['name']]['panel_cutout'][1] + profiles[printer['name']]['outer_panel_z_offset'] + profiles[printer['name']]['outer_panel_overlap_z'])/2-frames[printer_size][4]/2
                                                    ))
                                                )

                                                assm = cq.Assembly(name=f"_{name}")
                                                assm.add(_face_plate,  name="Face Plate", color=cq.Color("darkorchid4"))
                                                assm.add(_outer_plate, name="Outer",      color=cq.Color("gray18"))
                                                assm.add(frame,        name="Frame",      color=cq.Color("Gray"))

                                                for i, pos in enumerate(dock_positions):
                                                    assm.add(cq.importers.importStep(f"../supplements/{'Anthead' if dock['width'] == 60 else 'SB'}.step").rotate((0, 0, 0), (1, 0, 0), 90).translate(pos), name=f"Dock{i}", color=cq.Color("yellow"))

                                                cq.exporters.export(
                                                    assm.toCompound(),
                                                    os.path.join(img_path, f"{name}.svg"),
                                                    opt={
                                                        "width": 300,
                                                        "height": 300,
                                                        "marginLeft": 10,
                                                        "marginRight": 10,
                                                        "marginTop": 10,
                                                        "marginBottom": 10,
                                                        "showAxes": False,
                                                        "projectionDir": (0.0, 0.0, 1.0),
                                                        "strokeWidth": 0.5,
                                                        "strokeColor": (255, 0, 0),
                                                        "hiddenColor": (0, 0, 255),
                                                        "showHidden": True,
                                                    }
                                                )
                                                name = f"{printer['name'].title()}_{printer_size}_{dock['width']}mm_{tool_count}tools_{port_pos}_{port_type}_{mount_rail}_rail"
                                                valid_plates.append(
                                                    {
                                                        "name"        : name,
                                                        "printer_name": printer['name'],
                                                        "printer_size": printer_size,
                                                        "dock_width"  : dock['width'],
                                                        "tool_count"  : tool_count,
                                                        "port_pos"    : port_pos,
                                                        "port_type"   : port_type
                                                    }
                                                )

    # Export the CAD files
    print("Exporting CAD files")
    cad_path = os.path.join(parent_path, "CAD")
    makePath(cad_path)

    for printer in printers:
        for size in printer['sizes']:
            cad_file = os.path.join(cad_path, f"{size}mm {printer['name'].title()}.step")
            cad_zip  = os.path.join(cad_path, f"CAD - {size}mm {printer['name'].title()} Plates.zip")

            locals()[f"{printer['name']}_{size}_assm"].save(cad_file)

            # Zip the CAD file to save space
            print("Compressing CAD file")
            zip = zipfile.ZipFile(cad_zip, "w", zipfile.ZIP_DEFLATED)
            zip.write(cad_file, f"{size}mm {printer['name']}.step")
            zip.close()

            print("Removing Uncompressed CAD files")
            os.remove(cad_file)

    # Compress the SVG files
    print("Compressing SVG files")
    for f in [x for x in os.listdir(img_path) if x.endswith(".svg")]:
        temp      = f.replace(".svg", "_temp.svg")
        f_path    = os.path.join(img_path, f)
        temp_path = os.path.join(img_path, temp)

        class ScourOptions:
            pass

        options = ScourOptions
        input = open(f_path, "rb")
        output = open(temp_path, "wb")

        scour.start(options, input, output)

        os.remove(f_path)
        os.rename(temp_path, f_path)

        # Remove extra whitespace and add background
        with open(f_path, "r") as file:
            data = file.readlines()

        data[1] = data[1].replace("width=\"300\"", "width=\"240\"")
        data[1] = data[1].replace("height=\"300\"", "height=\"247\"")

        data.insert(2, "<rect fill=\"#FFFFFF\" height=\"247\"  width=\"240\" x=\"0\" y=\"0\"/>\n")

        with open(f_path, "w") as file:
            file.writelines(data)


if __name__ == "__main__":
    start = time.time()
    main()
    end = time.time()

    exit(end-start)
