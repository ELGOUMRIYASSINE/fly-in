import heapq

class test():
    pass

ts = test()

jj = [3, 4, 1, 6, 2, 7, 5, 8]
heapq.heapify(jj)


print([heapq.heappop(jj) for _ in range(7)])

# pq = []

# heapq.heappush(pq, 5)
# heapq.heappush(pq, 2)
# heapq.heappush(pq, 3)
# heapq.heappush(pq, 1)
# print(heapq.heappop(pq))
# print(heapq.heappop(pq))
# print(heapq.heappop(pq))
# print(heapq.heappop(pq))