import os

def collect_files(root_dir, extensions):
    """Recursively collect files with the given extensions."""
    collected_files = []
    for dirpath, _, filenames in os.walk(root_dir):
        for filename in filenames:
            if filename.lower().endswith(extensions):
                filepath = os.path.join(dirpath, filename)
                collected_files.append(filepath)
    return collected_files

def write_to_output(collected_files, output_file):
    """Write the contents of the collected files to the output file with delimiters."""
    with open(output_file, 'w', encoding='utf-8') as outfile:
        for filepath in collected_files:
            outfile.write(f"\n{'='*80}\n")
            outfile.write(f"File: {filepath}\n")
            outfile.write(f"{'='*80}\n\n")
            try:
                with open(filepath, 'r', encoding='utf-8') as infile:
                    contents = infile.read()
                    outfile.write(contents)
            except Exception as e:
                outfile.write(f"Error reading file: {e}\n")

def main():
    # Specify the root directory of your repository
    root_dir = '.'  # Change this to the path of your repository if needed

    # Specify the output file
    output_file = '_repository_contents.txt'

    # Define the file extensions to include
    extensions = ('.py', '.ipynb', '.ini', '.txt')

    # Collect the files
    collected_files = collect_files(root_dir, extensions)

    # Write to the output file
    write_to_output(collected_files, output_file)

    print(f"Collected {len(collected_files)} files. Contents written to '{output_file}'.")

if __name__ == "__main__":
    main()
