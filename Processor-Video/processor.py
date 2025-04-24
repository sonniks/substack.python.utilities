# processor.py
import argparse
import datetime
import os
import sys


from fileio import ensure_working_directory, cleanup_sequence
from logger import log
from videotoimage import extract_frames, frames_to_video


def define_args():
    """
    Define command-line arguments using argparse for the image/video processing script.
    :return:
    """
    parser = argparse.ArgumentParser(description="Image/Video Processor")
    parser.add_argument('--inputfile', required=True,
                        help='Input file (image, video, or image sequence dir)')
    parser.add_argument('--outputfile', required=True, help='Output file (image or video)')
    parser.add_argument('--operation', required=True,
                        choices=['negative', 'negative-reimage', 'chromakey'], help='Processing operation')
    parser.add_argument('--color',
                        help='Hex color string (e.g. #00ff00) for chromakey or negative-reimage')
    parser.add_argument('--workingdirectory',
                        required=True, help='Directory for temporary image sequences')
    parser.add_argument('--sequencename',
                        help='Optional label to append to generated sequence')
    parser.add_argument('--backgroundsequence', help='Background image or video or directory')
    parser.add_argument('--cleanup', action='store_true',
                        help='Delete image sequence files after processing')
    return parser.parse_args()


def is_video_file(path):
    """
    Check if the given path is a video file based on its extension.
    :param path:
    :return:
    """
    return path.lower().endswith(('.mp4', '.mov', '.avi', '.mkv', '.webm'))


def main():
    """
    Main function to process images or videos based on command-line arguments.
    :return:
    """
    args = define_args()
    timestamp = datetime.datetime.now().strftime('%Y%m%d%H%M')
    sequence_prefix = f"{timestamp}_{args.sequencename}" if args.sequencename else timestamp
    ensure_working_directory(args.workingdirectory)
    log("Processing begins")
    input_sequence_dir = args.inputfile
    output_sequence_dir = args.workingdirectory
    output_sequence_prefix = sequence_prefix
    if is_video_file(args.inputfile):
        input_sequence_dir = os.path.join(args.workingdirectory, "inputframes")
        ensure_working_directory(input_sequence_dir)
        log("Extracting frames from input video...")
        if not extract_frames(args.inputfile, input_sequence_dir, output_sequence_prefix):
            log("Failed to extract frames from input video.")
            return
    background_sequence_dir = args.backgroundsequence
    if args.backgroundsequence and is_video_file(args.backgroundsequence):
        background_sequence_dir = os.path.join(args.workingdirectory, "backgroundframes")
        ensure_working_directory(background_sequence_dir)
        log("Extracting frames from background video...")
        if not extract_frames(args.backgroundsequence, background_sequence_dir, output_sequence_prefix):
            log("Failed to extract frames from background video.")
            return
    if args.operation in ['negative', 'negative-reimage']:
        from negative import process as negative_process
        negative_process(
            inputfile=input_sequence_dir,
            outputfile=args.outputfile,
            operation=args.operation,
            color=args.color,
            workdir=args.workingdirectory,
            sequence_prefix=output_sequence_prefix
        )
    elif args.operation == 'chromakey':
        from chromakey import process as chroma_process
        chroma_process(
            inputfile=input_sequence_dir,
            outputfile=args.outputfile,
            keycolor=args.color,
            workdir=args.workingdirectory,
            sequence_prefix=output_sequence_prefix,
            background_sequence=background_sequence_dir
        )
    if is_video_file(args.outputfile):
        log("Reassembling frames into output video...")
        if not frames_to_video(args.workingdirectory, output_sequence_prefix, args.outputfile):
            log("Failed to assemble output video.")
            return
    if args.cleanup:
        cleanup_sequence(args.workingdirectory, output_sequence_prefix)
        log("Temporary sequence files cleaned up")


if __name__ == '__main__':
    main()
