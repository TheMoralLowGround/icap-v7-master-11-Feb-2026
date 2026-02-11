
def avg_distance(all_distance):
    # print(all_distance)
    avg_coverage = []
    count = 0
    total_distance = 0
    row_count = 0
    for i in all_distance:
        if len(i) > 0:
            row_count += 1
            count += len(i)
            s = round(sum(i) / 1200, 4)
            avg_coverage.append(s)
            # print(s)
            total_distance += s
            # print(total_distance)
        else:
            avg_coverage.append(0)
    """
    #print(row_count, count)
    if count!=0:
        return total_distance/len(all_distance)
    else:
        return 0
    """
    return avg_coverage
