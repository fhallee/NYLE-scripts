import argparse
import csv
import os
import parselmouth
import textgrids

def extract_formants_from_file(audio_file_path, textgrid_file_path, phones, desired_formants, points, include_following=False):
    """
    Args:
        audio_file_path (str): Path to the audio file
        textgrid_file_path (str): Path to the TextGrid file
        phones (list): A list of phone labels to extract formants for
        desired_formants (list): A list of integers specifying the formants to extract (e.g., [1, 2])
        points (list): A list of floats representing the time points (as proportions of the interval duration)
                       at which to extract formant values (e.g., [0.2, 0.5, 0.8])
        include_following (bool): Whether to include formant values for the following phone

    Returns:
        list: A list of dictionaries with "speaker", "phone", "point", "interval_start", "interval_end", "formant", and "formant_value" as columns
    """    
    sound = parselmouth.Sound(audio_file_path)
    grid = textgrids.TextGrid(textgrid_file_path)
    formants = sound.to_formant_burg(maximum_formant=5000)
    filename = os.path.basename(textgrid_file_path)

    formant_list = []

    for tier_name, tier in grid.items():
        if "phones" in tier_name:
            # Extracts the part before the first space
            speaker_from_tier = tier_name.split()[0]
            
            # Checks if this speaker name is in the filename
            if speaker_from_tier in filename:
                speaker_name = speaker_from_tier
                print(f"Processing speaker: {speaker_name}")
                
                for i, interval in enumerate(tier):
                    if interval.text in phones:  # Checks if the interval text matches any of the specified phones
                        current_phone = interval.text  # Stores the current phone being processed
                        
                        # Gets preceding and following phones
                        preceding_phone = tier[i-1].text if i > 0 else None
                        following_phone = tier[i+1].text if i < len(tier) - 1 else None
                        
                        for point in points:
                            formant_dict = {
                                "file": os.path.splitext(os.path.basename(audio_file_path))[0],
                                "speaker": speaker_name,
                                "phone": current_phone,
                                "preceding_phone": preceding_phone,
                                "following_phone": following_phone,
                                "point": point,
                                "interval_start": interval.xmin,
                                "interval_end": interval.xmax
                            }
                            
                            # Calculates time point within the interval
                            time_point = interval.xmin + (interval.xmax - interval.xmin) * point
                            
                            # Extracts formants for current phone
                            for formant_number in desired_formants:
                                formant_value = formants.get_value_at_time(int(formant_number), time_point)
                                formant_dict[f"F{formant_number}"] = formant_value
                            
                            # Extracts formants for following phone if it exists
                            if include_following and following_phone and i + 1 < len(tier):
                                following_interval = tier[i + 1]
                                following_time_point = following_interval.xmin + (following_interval.xmax - following_interval.xmin) * point
                                
                                for formant_number in desired_formants:
                                    following_formant_value = formants.get_value_at_time(int(formant_number), following_time_point)
                                    formant_dict[f"following_F{formant_number}"] = following_formant_value
                            
                            formant_list.append(formant_dict)
    return formant_list


def main():
    parser = argparse.ArgumentParser(description="Extracts formants from audio files")
    parser.add_argument(
        "--audio_path",
        type=str,
        required=True,
        help="Path to directory containing audio files"
    )
    parser.add_argument(
        "--textgrids_path",
        type=str,
        required=True,
        help="Path to directory containing Textgrid files"
    )
    parser.add_argument(
        "--output",
        type=str,
        required=True,
        help="Path and file name for output data"
    )
    parser.add_argument(
        "--phones",
        type=str,
        nargs='+',
        required=True,
        help="Phone(s) for analysis (e.g., --phone l or --phone l r s)"
    )
    parser.add_argument(
        "--formants",
        type=int,
        nargs='+',
        choices=[1, 2, 3, 4],
        required=True,
        help="Specify which formants to extract (e.g., 1 2)"
    )
    parser.add_argument(
        "--points",
        type=float,
        nargs='+',
        required=True,
        help="Specify the measurement points as percentages (e.g., 0.2 0.5). Up to 3 points allowed."
    )
    parser.add_argument(
        "--following_phone",
        action="store_true",
        help="Include formant measurements for the following phone"
    )

    args = parser.parse_args()

    if len(args.points) > 3:
        parser.error("You can specify up to 3 measurement points only.")

    audio_files = {os.path.splitext(f)[0]: os.path.join(args.audio_path, f) for f in os.listdir(args.audio_path) if f.endswith(".wav")}
    textgrid_files = {os.path.splitext(f)[0]: os.path.join(args.textgrids_path, f) for f in os.listdir(args.textgrids_path) if f.endswith(".TextGrid")}

    matched_files = set(audio_files.keys()) & set(textgrid_files.keys())
    if not matched_files:
        raise ValueError("No matching audio and TextGrid files found in the provided directories.")

    print("Starting processing")
    
    # Opens the output file and write header
    with open(args.output, 'w', newline='', encoding='utf-8') as csvfile:
        # We need to determine the fieldnames first by processing one file to see what formants are included
        first_file = next(iter(matched_files))
        first_audio_path = audio_files[first_file]
        first_textgrid_path = textgrid_files[first_file]
        
        print(f"Processing {first_file}")
        first_data = extract_formants_from_file(
            audio_file_path=first_audio_path,
            textgrid_file_path=first_textgrid_path,
            phones=args.phones,
            desired_formants=args.formants,
            points=args.points,
            include_following=args.following_phone
        )
        
        if first_data:
            fieldnames = list(first_data[0].keys())
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(first_data)
            
            # Processes remaining files
            remaining_files = matched_files - {first_file}
            for file_name in remaining_files:
                print(f"Processing {file_name}")
                audio_file_path = audio_files[file_name]
                textgrid_file_path = textgrid_files[file_name]
                formant_data = extract_formants_from_file(
                    audio_file_path=audio_file_path,
                    textgrid_file_path=textgrid_file_path,
                    phones=args.phones,
                    desired_formants=args.formants,
                    points=args.points,
                    include_following=args.following_phone
                )
                writer.writerows(formant_data)

    print(f"Formant data saved to {args.output}")

if __name__ == "__main__":
    main()