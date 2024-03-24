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

def main():
	parser = argparse.ArgumentParser()
	parser.add_argument("--down-angle", help="Servo angle when down",
			type=int, default=160)
	parser.add_argument("--down-delay", help="Servo down delay",
			type=int, default=100)
	parser.add_argument("--up-angle", help="Servo angle when up",
			type=int, default=146)
	parser.add_argument("--up-delay", help="Servo up delay",
			type=int, default=100)
	parser.add_argument("--merge-threshold",
			help="Distance between G1 and G0 moves that can be merged",
			type=float, default=0.2)
	parser.add_argument("--input", help="Gcode input file",
			type=str, required=True)
	parser.add_argument("--output", help="Gcode output file",
			type=str)
	args = parser.parse_args()


	with open(args.input, 'r') as f:
		gcode = f.read()

	gcode_parsed = GcodeParser(gcode)

	prev_line = None
	g1_command = ('G', 1)
	g0_command = ('G', 0)
	sync_gcode = GcodeLine(
			command=('G', 4),
			params={"P": 0},
			comment="Sync")
	servo_up_gcode =  GcodeLine(
			command=('M', 280),
			params={"P": 0, 'S': args.up_angle},
			comment="Servo Up")
	servo_up_delay_gcode = GcodeLine(
			command=('G', 4),
			params={"P": args.up_delay},
			comment="Wait servo up")
	servo_down_gcode =  GcodeLine(
			command=('M', 280),
			params={"P": 0, 'S': args.down_angle},
			comment="Servo Down")
	servo_down_delay_gcode = GcodeLine(
			command=('G', 4),
			params={"P": args.down_delay},
			comment="Wait servo down")

	for line in gcode_parsed.lines:
		# Consecutive G1/G0 commands
		if line.command == g0_command and (prev_line != None and prev_line.command == g1_command):
			if prev_line.params == line.params:
				continue

			if gcode_merge(args, prev_line.params, line.params):
				continue

		if line.command == g0_command:
			print(sync_gcode.gcode_str)
			print(servo_up_gcode.gcode_str)
			print(servo_up_delay_gcode.gcode_str)

		print(line.gcode_str)

		if line.command == g0_command:
			print(sync_gcode.gcode_str)
			print(servo_down_gcode.gcode_str)
			print(servo_down_delay_gcode.gcode_str)

		prev_line = line


if __name__ == "__main__":
	main()
