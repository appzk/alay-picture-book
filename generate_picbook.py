from generate_clips import generate_clips  
  
# 假设你已经有了 workflowfile 和 csv_file_path 的值  
workflowfile = 'sd3-picbook-workflow_api.json'  
csv_file_path = 'prompt.csv'  
  
generate_clips(workflowfile, csv_file_path)