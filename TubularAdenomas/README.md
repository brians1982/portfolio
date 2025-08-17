# Tubular Adenoma Project

Check out our first preprint [here](https://arxiv.org/abs/2508.09339)! One more planned for later in 2025 - stay tuned!

##

## Dataset Creation

I created the labeled dataset for this research project.  I was provided about 450 gigapixel-sized Whole Slide Images (WSIs) split between a Control set and a Case set.  I was also provided about 20 WSIs that had regions of relevant tissue annotated.  In order to extract the relevant tissue from the entire dataset efficiently, I trained a convolutional neural network (CNN) to identify whether a sample of tissue was relevant to the study or not.  I did this in two steps.  First, I extracted all tiles in a WSI that had tissue present, and recorded each tile's coordinates. I stored the images and the record in a ZIP file for each WSI.   

<img src="combined_1_resized.png" height="300"> <img src="combined_2_resized.png" height="300"> <img src="combined_3_resized.png" height="300"> 
