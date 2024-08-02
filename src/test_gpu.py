"""
Used to test TensorFlow's GPU usage and if it is running on the GPU or on CPU only.

To use, run this file directly.
"""

import tensorflow as tf

def main():
    
    # Get the list of available GPUs
    gpus = tf.config.list_physical_devices('GPU')
    
    # Print the number of GPUs detected by TensorFlow
    print(f"\nNumber of GPUs available: {len(gpus)}")
    
    # If GPUs are available, print some additional information
    if gpus:
        for gpu in gpus:
            print(f"GPU Name: {gpu.name}, Type: {gpu.device_type}")
        
        # Try to get memory info (this may not work on all systems)
        try:
            gpu_memory = tf.config.experimental.get_memory_info('GPU:0')
            print(f"GPU Memory: {gpu_memory['current'] / 1024**3:.2f} GB / {gpu_memory['peak'] / 1024**3:.2f} GB\n")
        except:
            print("Unable to retrieve GPU memory information.\n")
    else:
        print("No GPU available. TensorFlow will use CPU.\n")

if __name__ == "__main__":
    main()