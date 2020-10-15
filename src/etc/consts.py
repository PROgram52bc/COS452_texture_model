from os.path import dirname, abspath

ROOT_DIR = dirname(dirname(dirname(abspath(__file__))))

transformation_dir = ['src', 'transformations']
analysis_dir = ['src', 'analysis']
image_dir = ['images']
sorted_data_dir = ['data', 'sort']
metric_sorted_data_dir = [*sorted_data_dir, 'metrics']
human_sorted_data_dir = [*sorted_data_dir, 'humans']
ranked_data_dir = ['data', 'rank']
printable_dir = ['printables']
image_extensions = ['jpg', 'jpeg', 'png']

csv_subfield_delim = '#'  # delimiter for subfields in csv
agent_name_delim = '-'  # delimiter for separating agent type from agent name
