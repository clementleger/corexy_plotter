#!/usr/bin/python3
import argparse
import math
from gcodeparser import GcodeParser, GcodeLine

def gcode_merge(args, position_1, position_2):
	if (not ("X" in position_1 and "X" in position_2 and
	    "Y" in position_1 and "Y" in position_2)):
		return False

	dist = math.sqrt((position_2["X"] - position_1["X"]) ** 2 +
			 (position_2["Y"] - position_1["Y"]) ** 2)

	return (dist <= args.merge_threshold)

def gcode_output(file, cmd):
	file.write(cmd.gcode_str + "\n")

def is_g0(gcode):
	return gcode.command == ('G', 0)

def is_g1(gcode):
	return gcode != None and gcode.command == ('G', 1)

def gen_g4(delay, comment = None):
	return GcodeLine(command=('G', 4), params={"P": delay}, comment=comment)

def gen_m280(angle, comment = None):
	return GcodeLine(command=('M', 280), params={"P": 0, 'S': angle}, comment=comment)

def main():
	parser = argparse.ArgumentParser()
	parser.add_argument("--down-angle", help="Servo angle when down",
			type=int, default=160)
	parser.add_argument("--down-delay", help="Servo down delay",
			type=int, default=100)
	parser.add_argument("--up-angle", help="Servo angle when up",
			type=int, default=143)
	parser.add_argument("--up-delay", help="Servo up delay",
			type=int, default=100)
	parser.add_argument("--merge-threshold",
			help="Distance between G1 and G0 moves that can be merged",
			type=float, default=0.2)
	parser.add_argument("--input", help="Gcode input file",
			type=str, required=True)
	parser.add_argument("--output", help="Gcode output file",
			type=str, default="out.gcode")
	args = parser.parse_args()

	with open(args.input, 'r') as f:
		gcode = f.read()

	out = open(args.output, "w")

	parsed_gcode = GcodeParser(gcode)
	prev_line = GcodeLine(command=('X', 0), params={}, comment="")
	servo_up_sequence = [
		gen_g4(0, "Sync"),
		gen_m280(args.up_angle, "Servo up"),
		gen_g4(args.up_delay, "Wait servo up")
	]
	servo_down_sequence = [
		gen_g4(0, "Sync"),
		gen_m280(args.down_angle, "Servo down"),
		gen_g4(args.down_delay, "Wait servo down")
	]

	for line in parsed_gcode.lines:
		line_is_g0 = is_g0(line)
		# Consecutive G1/G0 commands
		if line_is_g0 and is_g1(prev_line):
			# Skip them if the position is the same
			if prev_line.params == line.params:
				continue

			if gcode_merge(args, prev_line.params, line.params):
				continue

		if line_is_g0:
			for s in servo_up_sequence:
				gcode_output(out, s)

		gcode_output(out, line)

		if line_is_g0:
			for s in servo_down_sequence:
				gcode_output(out, s)

		prev_line = line

	for s in servo_up_sequence:
		gcode_output(out, s)

	out.close()

if __name__ == "__main__":
	main()
