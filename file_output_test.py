import logging

# Write to a file instead of stdout
with open('file_output_test.log', 'w') as f:
    f.write('Test line 1\n')
    f.write('Test line 2\n')
    f.write('Test line 3\n')

# Also try logging to a file
logging.basicConfig(filename='file_output_test_logging.log', level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)
logger.info('Logging test line 1')
logger.info('Logging test line 2')
