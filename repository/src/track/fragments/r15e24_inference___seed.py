def _seed(use_torch):
    import random
    import numpy as np
    random.seed(SEED)
    np.random.seed(SEED)
    if use_torch:
        import torch
        torch.manual_seed(SEED)
        if torch.cuda.is_available():
            torch.cuda.manual_seed_all(SEED)
    return np
