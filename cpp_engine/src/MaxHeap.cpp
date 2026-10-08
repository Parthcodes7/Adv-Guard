#include "advguard.h"
#include <stdexcept>
#include <algorithm>

MaxHeap::MaxHeap(int k) : max_size(k) {}

void MaxHeap::heapifyUp(int index) {
    while (index > 0) {
        int parent = (index - 1) / 2;
        if (heap[parent] < heap[index]) {
            std::swap(heap[parent], heap[index]);
            index = parent;
        } else {
            break;
        }
    }
}

void MaxHeap::heapifyDown(int index) {
    int size = heap.size();
    while (index < size) {
        int left = 2 * index + 1;
        int right = 2 * index + 2;
        int largest = index;

        if (left < size && heap[largest] < heap[left]) {
            largest = left;
        }
        if (right < size && heap[largest] < heap[right]) {
            largest = right;
        }

        if (largest != index) {
            std::swap(heap[index], heap[largest]);
            index = largest;
        } else {
            break;
        }
    }
}

void MaxHeap::push(const Neighbor& neighbor) {
    if (heap.size() < max_size) {
        heap.push_back(neighbor);
        heapifyUp(heap.size() - 1);
    } else if (neighbor.distance < heap[0].distance) {
        heap[0] = neighbor;
        heapifyDown(0);
    }
}

const Neighbor& MaxHeap::top() const {
    if (heap.empty()) {
        throw std::out_of_range("Heap is empty");
    }
    return heap[0];
}

void MaxHeap::pop() {
    if (heap.empty()) return;
    heap[0] = heap.back();
    heap.pop_back();
    heapifyDown(0);
}

bool MaxHeap::isFull() const {
    return heap.size() == max_size;
}

int MaxHeap::size() const {
    return heap.size();
}

std::vector<Neighbor> MaxHeap::getElements() const {
    return heap;
}
