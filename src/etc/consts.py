from os.path import dirname, abspath

ROOT_DIR = dirname(dirname(dirname(abspath(__file__))))

transformation_dir = ['src', 'transformations']
analysis_dir = ['src', 'analysis']
image_dir = ['images']
sorted_data_dir = ['data', 'sort']
metric_sorted_data_dir = [*sorted_data_dir, 'metrics']
human_sorted_data_dir = [*sorted_data_dir, 'humans']
raw_sorted_data_dir = [*sorted_data_dir, 'raw'] # raw human data to be decoded into human_sorted_data_dir
ranked_data_dir = ['data', 'rank']
sequence_data_dir = ['data', 'sequence']
plot_data_dir = ['data', 'plot']
sequence_filename = "sequences.json"
printable_dir = ['printables']
image_extensions = ['jpg', 'jpeg', 'png']
seq_num_formatter = "{:02d}".format # usage: seq_num_formatter(int_number), will ensure a width of 2 by padding zero

csv_subfield_delim = '#'  # delimiter for generic subfields in csv
agent_name_delim = '-'  # delimiter for separating agent type from agent name
