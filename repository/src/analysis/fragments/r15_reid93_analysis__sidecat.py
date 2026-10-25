def sidecat(support):
    a=support['spatial_regions'][support['spatial_source_zone']]['frame_count']>0
    b=support['spatial_regions'][support['spatial_target_zone']]['frame_count']>0
    return 'both' if a and b else 'before_only' if a else 'after_only' if b else 'neither'
