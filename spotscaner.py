#!/opt/homebrew/bin/python3.11
#
# This is a Python script of the SpotScaner, written by Kento Yanagisawa.
# Import libraries
import argparse
import csv
import cv2
import datetime
import glob
import numpy as np
import os
import os.path
import shutil
import sys

SpotScaner_version = 'v6.1.0'

# Function definition
def SpotScaner_single(plate_img, threshold10, marker_master, input_time, analyze_mode):
    file = glob.glob(plate_img)
    if len(file) == 0:
        print('Can\'t Find the inputted image in this directory!!!')
        print('')
        sys.exit()
    threshold = threshold10 / 10
    img_dir = os.path.dirname(plate_img)
    os.chdir(img_dir)
    img_name = os.path.splitext(os.path.basename(plate_img))[0]
    img_name2 = os.path.basename(plate_img)
    print('> Analyzing ' + img_name2)
    img_raw = cv2.imread(plate_img)  # Import an experimental result
    img = cv2.cvtColor(img_raw, cv2.COLOR_BGR2GRAY)
    # Find Marker in the experimental result
    mkr_list = range(100, 0, -5)
    for try_mkr in mkr_list:
        if try_mkr == 0:
            print('---> Can\'t Find any Markers in the Image!!!')
            print('---------------------')
            return img_name2
        else:
            try:
                mkr = cv2.resize(marker_master, (try_mkr, try_mkr))
                res = cv2.matchTemplate(img, mkr, cv2.TM_CCOEFF_NORMED)  # Get coordinate of marker in the result
                loc = np.where(res >= threshold)  # Trim coordinates less than threshold
                mark_area = {
                    'top_x': min(loc[1]),
                    'top_y': min(loc[0]),
                    'bottom_x': max(loc[1]),
                    'bottom_y': max(loc[0])
                }
                img = img[mark_area['top_y']:mark_area['bottom_y'], mark_area['top_x']:mark_area['bottom_x']]
            except ValueError:
                pass
            else:
                print('---> Marker (' + str(try_mkr) + '^2) Match!!!')
                break
    res, img = cv2.threshold(img, 150, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
    # Convert the image to black and white image with 50 as threshold
    res_name = img_name + '_converted.png'
    try:
        # Invert the converted image for print
        img_inverted = cv2.bitwise_not(img)
        cv2.imwrite(res_name, img_inverted)  # Output Converted image after Inverted
    except cv2.error:
        print('---> However, Can\'t Crop the Image!!!')
        print('---------------------')
        return img_name2
    else:
        print('---> Output' + ' ' + res_name)
    if analyze_mode == 'replicator':  # Spot-test with Replicator (8*12 matrix)
        n_col = 12  # Number of spots per column
        n_row = 8  # Number of spots per row
    if analyze_mode == 'pipette':  # Spot-test with Pipette (4*6 matrix)
        n_col = 6  # Number of spots per column
        n_row = 4  # Number of spots per row
    margin_top = 1  # Number for north-west marker's row
    n_row = n_row + margin_top  # Number of spots per row + north-west marker's row
    img = cv2.resize(img, (n_col * 100, n_row * 100))  # Resize based on the number of matrices
    csv_name_time = img_name + '_results.csv'  # Make CSV file for data collection
    result_csv = os.path.join(img_dir, csv_name_time)
    with open(result_csv, 'w', encoding='UTF-8') as f:
        writer = csv.writer(f)
        writer.writerow(['Time', 'Image', 'Threshold', 'row', 'column', 'Colony'])
    csv_raw = []
    for row in range(margin_top, n_row):  # Analyze in order from the top row
        for col in range(n_col):  # Analyze in order from the leftmost column
            colony_position = col + 1
            tmp_img = img[row * 100:(row + 1) * 100, col * 100:(col + 1) * 100]  # Cut out one spot area
            whole_area = tmp_img.size  # Get the number of pixels in the entire cropped spot area
            white_area = cv2.countNonZero(tmp_img) / whole_area * 100
            # Get the number of pixels in the white area that the area covered by the colony
            csv_raw.append([input_time.strftime('%Y-%m-%d %H:%M:%S'),
                            img_name,
                            threshold10,
                            row,
                            colony_position,
                            round(white_area, 2)
                            ])
    with open(result_csv, 'a') as f:
        writer = csv.writer(f)
        writer.writerows(csv_raw)
    csv_path, csv_name = os.path.split(result_csv)
    print('---> Summarize results & Output ' + csv_name)
    print('---------------------')

def SpotScaner_multi(plate_dir, threshold, marker_master, input_time, analyze_mode):
    img_ext = ['*.jpg', '*.JPG', '*.jpeg']
    files = []
    for ext in img_ext:
        path = os.path.join(plate_dir, ext)
        files.extend(glob.glob(path))
    if len(files) == 0:
        print('Can\'t Find any images (*.jpg/*.JPG/*.jpeg) in this directory!!!')
        print('')
        sys.exit()
    for file in files:
        SpotScaner_single(file, threshold, marker_master, input_time, analyze_mode)
    converted_path = os.path.join(plate_dir, 'converted_' + input_time.strftime('%Y-%m-%d_%H-%M-%S'))
    os.mkdir(converted_path)
    move_img_list = glob.glob('./*_converted.png')
    for item in move_img_list:
        item = item.replace('./', '')
        moved_file_path = os.path.join(converted_path, item)
        shutil.move(item, moved_file_path)
    csv_path = os.path.join(plate_dir, 'results_' + input_time.strftime('%Y-%m-%d_%H-%M-%S'))
    os.mkdir(csv_path)
    move_csv_list = glob.glob('./*_results.csv')
    for item in move_csv_list:
        item = item.replace('./', '')
        moved_file_path = os.path.join(csv_path, item)
        shutil.move(item, moved_file_path)

def SpotScaner_marker():
    # Generate Maker Image
    marker_image = np.full((975, 975, 1), 255, dtype=np.uint8)
    cv2.rectangle(marker_image, (1, 1), (974, 974), 0, thickness=2)
    cv2.rectangle(marker_image, (150, 150), (825, 825), 0, cv2.FILLED)
    cv2.rectangle(marker_image, (368, 368), (607, 607), 255, cv2.FILLED)
    cv2.imwrite('marker_image.png', marker_image)
    TeXsource = '\\documentclass[paper=A4, head_space=20mm, foot_space=20mm, article, jafontsize=12Q, jafontscale=0.92, final]{jlreq} %2 up\n'\
	            '\n'\
                '\\usepackage[no-math]{fontspec}\n'\
                '\\usepackage[hiresbb]{graphicx}\n'\
                '\\usepackage[dvipsnames]{xcolor}\n'\
                '\\usepackage{tikz}\n'\
                '\\usepackage[\n'\
                '   unicode,%\n'\
                '   bookmarks=true, %\n'\
                '   bookmarksnumbered=true,%\n'\
                '   pdfusetitle,%\n'\
                '   pdflang=ja-JP, %\n'\
                '   hidelinks%\n'\
                ']{hyperref}\n'\
                '\\pagestyle{empty}\n'\
                '\n'\
                '\\title{SpotScaner v6.1.0}\n'\
                '\\author{Kento Yanagisawa}\n'\
                '\n'\
                '\\begin{document}\n'\
                '   \\begin{center}\n'\
                '      \\tikzset{\n'\
                '         TargetMarker/.pic={\n'\
                '            \\draw[anchor = south west](-0.9, -0.9) node{\\includegraphics[width = 0.45cm]{marker_image.png}};\n'\
                '         }\n'\
                '      }\n'\
                '      \\begin{tikzpicture}[x = 1mm, y = 1mm]\n'\
                '            \\filldraw[black](-10, -10) rectangle (137.5, 95);\n'\
                '%%%            \\draw[step = 1, lightgray](-10, -10) grid(140, 100);\n'\
                '%%%            \\draw[step = 10, gray](-10, -10) grid(140, 100);\n'\
                '            \\draw[white](64, 90) node{\\fontspec{Monaco}spotscaner --analyze replicator [-t {1,2,3,4,5,6,7,8,9,10}]};\n'\
                '%            \\pic at (7.5, 79.5) {TargetMarker};\n'\
                '            \\pic at (3.5, 79.5) {TargetMarker};\n'\
                '            \\pic at (115.5, 79.5) {TargetMarker};\n'\
                '            \\pic at (115.5, -1.5) {TargetMarker};\n'\
                '            \\foreach \\x in {10, 19, ..., 117} \\foreach \\y in {10, 19, ..., 73} \\draw[line width = 0.5pt, gray](\\x, \\y) circle(2);\n'\
                '            \\draw[white](64, -5) node{\\footnotesize\\fontspec{Monaco}SpotScaner v6.1.0, Coordinated by Kento Yanagisawa};\n'\
                '      \\end{tikzpicture}\n'\
                '   \\end{center}\n'\
                '      \\vspace{40mm}\n'\
                '   \\begin{center}\n'\
                '      \\tikzset{\n'\
                '         TargetMarker/.pic={\n'\
                '            \\draw[anchor = south west](-1.1, -1.1) node{\\includegraphics[width = 0.35cm]{marker_image.png}};\n'\
                '         }\n'\
                '      }\n'\
                '      \\begin{tikzpicture}[x = 1mm, y = 1mm]\n'\
                '            \\filldraw[black](-10, -10) rectangle (137.5, 95);\n'\
                '%            \\draw[step = 1, lightgray](-10, -10) grid(140, 100);\n'\
                '%            \\draw[step = 10, gray](-10, -10) grid(140, 100);\n'\
                '%            \\draw[step = 9.6, blue, shift={(21.81, -0.2)}](0, 0) grid(86.4, 86.4);\n'\
                '            \\draw[white](64, 90) node{\\fontspec{Monaco}spotscaner --analyze pipette [-t {1,2,3,4,5,6,7,8,9,10}]};\n'\
                '%            \\pic at (7.5, 79.5) {TargetMarker};\n'\
                '            \\pic[scale = 0.8] at (35.5, 64) {TargetMarker};\n'\
                '            \\pic[scale = 0.8] at (94.5, 64) {TargetMarker};\n'\
                '            \\pic[scale = 0.8] at (94.5, 19) {TargetMarker};\n'\
                '%            \\foreach \\x in {41.012, 50.612, ..., 98} \\foreach \\y in {28.6, 38.2, ..., 60} \\draw[line width = 0.5pt, gray](\\x, \\y-1.5) --(\\x, \\y+1.5);\n'\
                '%            \\foreach \\x in {41.012, 50.612, ..., 98} \\foreach \\y in {28.6, 38.2, ..., 60} \\draw[line width = 0.5pt, gray](\\x-1.5, \\y) --(\\x+1.5, \\y);\n'\
                '            \\draw[line width = 1pt, white](65, 43) circle(44);\n'\
                '            \\draw[white](64, -5) node{\\footnotesize\\fontspec{Monaco}SpotScaner v6.1.0, Coordinated by Kento Yanagisawa};\n'\
                '      \\end{tikzpicture}\n'\
                '   \\end{center}\n'\
                '\\end{document}'
    with open('SpotScaner_marker.tex', 'w', encoding='UTF-8') as f:
        f.write(TeXsource)

def SpotScaner_citation():
    TeXsource = '@Manual{spotscaner,\n'\
                '    title = {SpotScaner: Recognize \\& Analyze images of Spot-test in Fungal Genetics},\n'\
                '    author = {Kento Yanagisawa},\n'\
                '    year = {2023},\n'\
                '    note = {' + SpotScaner_version + '},\n'\
                '    url = {https://github.com/KentoYana/spotscaner},\n'\
                '  }'
    with open('SpotScaner_citation.bib', 'w', encoding='UTF-8') as f:
        f.write(TeXsource)

# Command line setting
parser = argparse.ArgumentParser()
mode = parser.add_mutually_exclusive_group()
image = parser.add_mutually_exclusive_group()
parser.add_argument('-v', '--version', action='store_true',
                    help="show version, citation and exit")
parser.add_argument('-e', '--example', action='store_true',
                    help="show usage example and exit")
parser.add_argument('-g', '--generate', choices=['marker', 'cite'],
                    help='open the file chosen this option')
mode.add_argument('-a', '--analyze', choices=['pipette', 'replicator'],
                  help='chose analyzing mode (pipette: 4*6 matrix, replicator: 8*12 matrix)')
image.add_argument('-s', '--single',
                   help='analyze only the inputted image.')
image.add_argument('-m', '--multi', action='store_true',
                   help='analyze all images in the current directory')
parser.add_argument('-t', '--threshold', type=int, choices=range(1, 11),
                    help='threshold for marker recognition(default: 7)')

args = parser.parse_args()
pwd = os.getcwd()
initial_time = datetime.datetime.now()

if args.version:
    print('SpotScaner ' + SpotScaner_version)
    print('Citation -> '
          'Kento Yanagisawa. '
          'SpotScaner: Recognize & Analyze images of Spot-test in Fungal Genetics, 2023. '
          + SpotScaner_version)
    sys.exit()
if args.example:
    print('')
    print('usage:')
    print('   spotscaner [-a {pipette,replicator}] [-s SINGLE | -m] [-t {1,2,3,4,5,6,7,8,9,10}]')
    print('example:')
    print('   spotscaner -a pipette -m')
    print('   spotscaner -a pipette -s spot-test.jpg')
    print('   spotscaner -a pipette -s spot-test.jpg -t 6')
    print('')
    sys.exit()
if args.generate:
    if args.generate == 'marker':
        SpotScaner_marker()
        print('---> Output SpotScaner_marker.tex & marker_image.png')
        print('To generate SpotScaner_marker.pdf, you need to use LaTeX.')
        print('Please run "lualatex SpotScaner_marker.tex" command on your computer.')
        print('If you don\'t have LaTeX environment, access to Overleaf (https://www.overleaf.com) and compile files')
    elif args.generate == 'cite':
        SpotScaner_citation()
        print('---> Output SpotScaner_citation.bib')
    print('')
    sys.exit()
if args.analyze:
    # Generate Maker Image
    marker = np.full((975, 975, 1), 255, dtype=np.uint8)
    cv2.rectangle(marker, (1, 1), (974, 974), 0, thickness=2)
    cv2.rectangle(marker, (150, 150), (825, 825), 0, cv2.FILLED)
    cv2.rectangle(marker, (368, 368), (607, 607), 255, cv2.FILLED)
    if args.analyze == 'replicator':
        print('')
        print('Analysis of Spot-test with Replicator (8*12 matrix)')
        print('')
        print('---------------------')
    elif args.analyze == 'pipette':
        print('')
        print('Analysis of Spot-test with Pipette (4*6 matrix)')
        print('')
        print('---------------------')
    if args.threshold:
        input_threshold = args.threshold
    else:
        input_threshold = 7
    if args.single:
        SpotScaner_single(os.path.join(pwd, args.single), input_threshold, marker, initial_time, args.analyze)
    elif args.multi:
        SpotScaner_multi(pwd, input_threshold, marker, initial_time, args.analyze)
    print('')
    print('Please look *_converted.png & check recognized the correct region or not.')
else:
    print('')
    print('This is the SpotScaner ' + SpotScaner_version + ', Coordinated by Kento Yanagisawa.')
    print('> Take a photo of spot-test plate with the printed marker,')
    print('> and then run this command. You can get a results.csv')
    parser.print_help()
