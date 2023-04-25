from PIL import Image
import os
import multiprocessing
import queue
import time

input_dir = '/home/killuh/Downloads/imgs_to_resize'
output_dir = '/home/killuh/Downloads/resized_imgs'
target_size = (1920, 1080)
num_processes = 16

# Split the file list into num_processes sub-lists
def split_files(file_list, num_processes):
    split_size = (len(file_list) + num_processes - 1) // num_processes # Round up to the nearest integer
    return [file_list[i:i+split_size] for i in range(0, len(file_list), split_size)]

# Worker function that resizes images in a sub-list of files
def resize_images(files, in_queue, out_queue):
    for filename in files:
        if filename.endswith('.jpg') or filename.endswith('.png'): # Check for image files
            with Image.open(os.path.join(input_dir, filename)) as img:
                in_queue.put(1) # Put a number on the queue to signal that we need a unique filename
                while out_queue.empty():
                    pass
                unique_num = out_queue.get() # Get a unique number from the queue
                new_filename = f"{unique_num}.jpg" # Generate a new filename
                # print(f"{img.size=} {target_size=}")
                if img.size[0] >= target_size[0] or img.size[1] >= target_size[1]: # Check if image needs to be resized
                    img.thumbnail(target_size) # Resize the image
                    rimg = img.resize(target_size, resample=Image.Resampling.BILINEAR)
                    # print(f"New size: {rimg.size=}")
                rimg.save(os.path.join(output_dir, new_filename)) # Save the resized image to the output directory

# Queue manager function that puts unique numbers on the queue when requested by workers
def manage_queue(in_queue, out_queue):
    unique_num = 0
    while True:
        if not in_queue.empty():
            in_queue.get() # Remove the number from the queue that triggered this function call
            unique_num += 1
            out_queue.put(unique_num) # Put the next unique number on the queue

if __name__ == '__main__':
    start_time = time.perf_counter()

    file_list = os.listdir(input_dir)
    file_lists = split_files(file_list, num_processes)

    in_queue = multiprocessing.Queue() #  w/ respect to unique manager
    out_queue = multiprocessing.Queue()

    # Start the queue manager process
    queue_process = multiprocessing.Process(target=manage_queue, args=(in_queue, out_queue,))
    queue_process.start()

    # Start the worker processes
    processes = []
    for i in range(num_processes):
        p = multiprocessing.Process(target=resize_images, args=(file_lists[i], in_queue, out_queue,))
        processes.append(p)
        p.start()

    # Wait for all worker processes to complete
    for p in processes:
        p.join()

    # Terminate the queue manager process
    queue_process.terminate()
    print(f"Total time elapsed: {time.perf_counter() - start_time:.2f} seconds")
