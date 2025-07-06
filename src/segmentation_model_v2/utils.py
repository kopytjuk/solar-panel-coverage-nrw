import torch


def determine_torch_device() -> torch.device:
    """In case user does not provide a desired device, this functions selects
    a device based on the machine's capabilities.

    Returns:
        torch.device: selected device
    """
    if torch.backends.mps.is_available():
        print("Metal Performance Shaders (MPS) backend is available!")
        device = torch.device("mps")
    elif torch.cuda.is_available():
        print("CUDA is available!")
        device = torch.device("cuda:0")
    else:
        print("No GPU acceleration available, falling back to CPUs!")
        device = torch.device("cpu")
    return device
