cd<template>
  <div
    ref="canvasContainer"
    class="w-full h-full relative overflow-hidden"
    :class="{
      'ring-4 ring-blue-400 ring-opacity-50': isDragOver,
      'cursor-grab': !mouseState.isDragging,
      'cursor-grabbing': mouseState.isDragging && !selectionBox,
    }"
    @drop="onDrop"
    @dragover.prevent="onDragOver"
    @dragenter.prevent="onDragEnter"
    @dragleave="onDragLeave"
    @contextmenu.prevent="onRightClick"
    @mouseup="onCanvasMouseUp"
  >
    <!-- Loading state while canvas initializes -->
    <div
      v-if="canvasSize.width === 0 || canvasSize.height === 0"
      class="absolute inset-0 flex items-center justify-center bg-gray-50"
    >
      <div class="text-gray-500">
        <svg class="animate-spin h-8 w-8 mx-auto mb-2" fill="none" viewBox="0 0 24 24">
          <circle
            class="opacity-25"
            cx="12"
            cy="12"
            r="10"
            stroke="currentColor"
            stroke-width="4"
          ></circle>
          <path
            class="opacity-75"
            fill="currentColor"
            d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"
          ></path>
        </svg>
        <p class="text-sm">Initializing canvas...</p>
      </div>
    </div>

    <v-stage
      v-if="canvasSize.width > 0 && canvasSize.height > 0"
      ref="stage"
      :config="{
        width: canvasSize.width,
        height: canvasSize.height,
        draggable: false,
        scaleX: scale,
        scaleY: scale,
        x: position.x,
        y: position.y,
      }"
      @wheel="onWheel"
      @mousedown="onStageMouseDown"
      @mousemove="onStageMouseMove"
      @mouseup="onStageMouseUp"
    >
      <!-- Background Grid -->
      <v-layer ref="gridLayer">
        <v-group v-if="showGrid">
          <v-line
            v-for="(line, index) in gridLines.vertical"
            :key="`v-${index}`"
            :config="{
              points: line,
              stroke: '#e5e7eb',
              strokeWidth: 1,
              opacity: 0.5,
            }"
          />
          <v-line
            v-for="(line, index) in gridLines.horizontal"
            :key="`h-${index}`"
            :config="{
              points: line,
              stroke: '#e5e7eb',
              strokeWidth: 1,
              opacity: 0.5,
            }"
          />
        </v-group>
      </v-layer>

      <!-- Connections Layer -->
      <v-layer ref="connectionsLayer">
        <v-line
          v-for="connection in renderConnections"
          :key="`connection-${connection.id}`"
          :config="{
            points: connection.points,
            stroke: selectedConnection === connection.id ? '#1d4ed8' : '#3b82f6',
            strokeWidth: selectedConnection === connection.id ? 4 : 2,
            opacity: selectedConnection === connection.id ? 1 : 0.8,
            hitStrokeWidth: 10,
          }"
          @click="onConnectionClick(connection, $event)"
          @contextmenu="onConnectionRightClick(connection, $event)"
          @mouseenter="onConnectionMouseEnter"
          @mouseleave="onConnectionMouseLeave"
        />
      </v-layer>

      <!-- Devices Layer -->
      <v-layer ref="devicesLayer">
        <v-group
          v-for="device in deviceStore.devices"
          :key="`device-${device.id}`"
          :config="{
            x: device.position_x,
            y: device.position_y,
            draggable: true,
          }"
          @dragstart="onDeviceDragStart(device)"
          @dragmove="onDeviceDragMove(device, $event)"
          @dragend="onDeviceDragEnd(device, $event)"
          @click="onDeviceClick(device, $event)"
          @dblclick="onDeviceDoubleClick(device)"
          @mousedown="onDeviceMouseDown(device, $event)"
          @mouseenter="onDeviceMouseEnter"
          @mouseleave="onDeviceMouseLeave"
        >
          <!-- Device Background -->
          <v-rect
            :config="{
              width: DEVICE_SIZE,
              height: DEVICE_SIZE,
              fill: getDeviceColor(device.device_type),
              stroke:
                selectedDevice?.id === device.id || selectedDevices.has(device.id)
                  ? '#1d4ed8'
                  : '#6b7280',
              strokeWidth:
                selectedDevice?.id === device.id || selectedDevices.has(device.id) ? 3 : 1,
              cornerRadius: 8,
              shadowColor: 'black',
              shadowBlur: 4,
              shadowOpacity: 0.1,
              shadowOffsetY: 2,
            }"
          />

          <!-- Device Icon -->
          <v-image
            v-if="getDeviceIcon(device)"
            :config="{
              x: 16,
              y: 16,
              width: 28,
              height: 28,
              image: getDeviceIcon(device),
            }"
          />

          <!-- Device Name -->
          <v-text
            :config="{
              x: 0,
              y: DEVICE_TEXT_Y_OFFSET,
              text: device.name,
              fontSize: 9,
              align: 'center',
              fill: '#374151',
              fontFamily: 'Arial',
              width: DEVICE_SIZE,
              ellipsis: true,
            }"
          />

          <!-- Connection Points -->
          <v-circle
            v-for="(point, index) in getConnectionPoints(device)"
            :key="`point-${device.id}-${index}`"
            :config="{
              x: point.x,
              y: point.y,
              radius: 4,
              fill: '#10b981',
              stroke: '#065f46',
              strokeWidth: 1,
              opacity: connectionMode ? 1 : 0,
            }"
            @click="onConnectionPointClick(device, point, $event)"
          />
        </v-group>
      </v-layer>

      <!-- Shapes Layer -->
      <v-layer ref="shapesLayer">
        <v-group
          v-for="shape in shapesStore.shapes"
          :key="`shape-${shape.id}`"
          :config="{
            x: shape.position_x,
            y: shape.position_y,
            draggable: true,
          }"
          @dragend="onShapeDragEnd(shape, $event)"
          @click="handleShapeClick(shape, $event)"
          @contextmenu="onShapeRightClick(shape, $event)"
        >
          <v-rect
            v-if="shape.shape_type === 'rectangle'"
            :config="{
              width: shape.width,
              height: shape.height,
              fill: shape.fill_color || '#93c5fd',
              stroke: selectedShapes.has(shape.id) ? '#1d4ed8' : (shape.stroke_color || '#3b82f6'),
              strokeWidth: selectedShapes.has(shape.id) ? 3 : (shape.stroke_width || 2),
            }"
          />
          <v-circle
            v-else-if="shape.shape_type === 'circle'"
            :config="{
              x: shape.width / 2,
              y: shape.height / 2,
              radius: shape.width / 2,
              fill: shape.fill_color || '#93c5fd',
              stroke: selectedShapes.has(shape.id) ? '#1d4ed8' : (shape.stroke_color || '#3b82f6'),
              strokeWidth: selectedShapes.has(shape.id) ? 3 : (shape.stroke_width || 2),
            }"
          />
        </v-group>
        <v-transformer ref="transformer" />
      </v-layer>

      <!-- Selection Layer -->
      <v-layer ref="selectionLayer">
        <v-rect
          v-if="selectionBox"
          :config="{
            x: Math.min(selectionBox.startX, selectionBox.endX),
            y: Math.min(selectionBox.startY, selectionBox.endY),
            width: Math.abs(selectionBox.endX - selectionBox.startX),
            height: Math.abs(selectionBox.endY - selectionBox.startY),
            fill: 'rgba(59, 130, 246, 0.1)',
            stroke: '#3b82f6',
            strokeWidth: 1,
            dash: [5, 5],
          }"
        />
      </v-layer>
    </v-stage>

    <!-- Context Menu -->
    <Transition
      enter-active-class="transition-all duration-200 ease-out"
      enter-from-class="opacity-0 scale-95 translate-y-1"
      enter-to-class="opacity-100 scale-100 translate-y-0"
      leave-active-class="transition-all duration-150 ease-in"
      leave-from-class="opacity-100 scale-100 translate-y-0"
      leave-to-class="opacity-0 scale-95 translate-y-1"
    >
      <div
        v-if="contextMenu.show"
        :style="{
          position: 'absolute',
          left: contextMenu.x + 'px',
          top: contextMenu.y + 'px',
          zIndex: 1000,
        }"
        class="bg-white/95 backdrop-blur-md border border-gray-200/60 rounded-lg shadow-2xl shadow-black/10 py-1 min-w-44"
        data-context-menu="true"
      >
        <div v-for="item in contextMenuItems" :key="item.label" class="relative context-menu-item">
          <button
            @click="item.submenu ? null : item.action()"
            class="w-full text-left px-3 py-1.5 text-xs text-gray-700 hover:bg-blue-50/80 hover:text-blue-900 flex items-center justify-between transition-all duration-150 ease-out"
            :class="{
              'cursor-default': item.submenu,
              'hover:bg-gradient-to-r hover:from-blue-50/80 hover:to-indigo-50/80': !item.submenu,
            }"
          >
            <div class="flex items-center space-x-2">
              <span class="text-sm opacity-70 transition-opacity">{{ item.icon }}</span>
              <span class="font-medium">{{ item.label }}</span>
            </div>
            <span v-if="item.submenu" class="text-gray-400 transition-colors">
              <svg class="w-2.5 h-2.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path
                  stroke-linecap="round"
                  stroke-linejoin="round"
                  stroke-width="2"
                  d="M9 5l7 7-7 7"
                ></path>
              </svg>
            </span>
          </button>

          <!-- Submenu -->
          <div
            v-if="item.submenu"
            class="submenu absolute left-full top-0 bg-white/95 backdrop-blur-md border border-gray-200/60 rounded-lg shadow-2xl shadow-black/10 py-1 min-w-36 z-10"
            data-context-menu="true"
          >
            <div v-for="subItem in item.submenu" :key="subItem.label" class="relative context-menu-item">
              <button
                @click="subItem.submenu ? null : subItem.action()"
                class="w-full text-left px-3 py-1.5 text-xs text-gray-700 hover:bg-gradient-to-r hover:from-blue-50/80 hover:to-indigo-50/80 hover:text-blue-900 flex items-center justify-between transition-all duration-150 ease-out"
                :class="{
                  'cursor-default': subItem.submenu
                }"
              >
                <div class="flex items-center space-x-2">
                  <span class="text-xs opacity-70">{{ subItem.icon }}</span>
                  <span class="font-medium">{{ subItem.label }}</span>
                </div>
                <span v-if="subItem.submenu" class="text-gray-400 transition-colors">
                  <svg class="w-2.5 h-2.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path
                      stroke-linecap="round"
                      stroke-linejoin="round"
                      stroke-width="2"
                      d="M9 5l7 7-7 7"
                    ></path>
                  </svg>
                </span>
              </button>

              <!-- Nested Submenu (Level 3) -->
              <div
                v-if="subItem.submenu"
                class="submenu absolute left-full top-0 bg-white/95 backdrop-blur-md border border-gray-200/60 rounded-lg shadow-2xl shadow-black/10 py-1 min-w-36 z-10"
                data-context-menu="true"
              >
                <div v-for="nestedItem in subItem.submenu" :key="nestedItem.label" class="relative context-menu-item">
                  <button
                    @click="nestedItem.submenu ? null : nestedItem.action()"
                    :disabled="nestedItem.disabled"
                    class="w-full text-left px-3 py-1.5 text-xs flex items-center justify-between transition-all duration-150 ease-out"
                    :class="{
                      'text-gray-400 cursor-not-allowed opacity-50': nestedItem.disabled,
                      'text-gray-700 hover:bg-gradient-to-r hover:from-blue-50/80 hover:to-indigo-50/80 hover:text-blue-900': !nestedItem.disabled && !nestedItem.submenu,
                      'cursor-default': nestedItem.submenu
                    }"
                  >
                    <div class="flex items-center space-x-2">
                      <span class="text-xs opacity-70">{{ nestedItem.icon }}</span>
                      <span class="font-medium">{{ nestedItem.label }}</span>
                    </div>
                    <span v-if="nestedItem.submenu" class="text-gray-400 transition-colors">
                      <svg class="w-2.5 h-2.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path
                          stroke-linecap="round"
                          stroke-linejoin="round"
                          stroke-width="2"
                          d="M9 5l7 7-7 7"
                        ></path>
                      </svg>
                    </span>
                  </button>

                  <!-- Fourth Level Submenu -->
                  <div
                    v-if="nestedItem.submenu"
                    class="submenu absolute left-full top-0 bg-white/95 backdrop-blur-md border border-gray-200/60 rounded-lg shadow-2xl shadow-black/10 py-1 min-w-36 z-10"
                    data-context-menu="true"
                  >
                    <button
                      v-for="deepItem in nestedItem.submenu"
                      :key="deepItem.label"
                      @click="deepItem.disabled ? null : deepItem.action()"
                      :disabled="deepItem.disabled"
                      class="w-full text-left px-3 py-1.5 text-xs flex items-center space-x-2 transition-all duration-150 ease-out"
                      :class="deepItem.disabled
                        ? 'text-gray-400 cursor-not-allowed opacity-50'
                        : 'text-gray-700 hover:bg-gradient-to-r hover:from-blue-50/80 hover:to-indigo-50/80 hover:text-blue-900'"
                    >
                      <span class="text-xs opacity-70">{{ deepItem.icon }}</span>
                      <span class="font-medium">{{ deepItem.label }}</span>
                    </button>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </Transition>

    <!-- Device Search Input -->
    <div v-if="showDeviceSearch" class="absolute bottom-4 right-16 z-10">
      <div class="relative">
        <input
          ref="deviceSearchInput"
          v-model="deviceSearchQuery"
          type="text"
          placeholder="Search device..."
          class="w-48 px-3 py-2 pr-8 text-sm bg-white border border-gray-200 rounded-lg shadow-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
          @keydown.enter="searchAndCenterDevice"
          @keydown.escape="closeDeviceSearch"
          @blur="closeDeviceSearch"
        />
        <button
          @click="closeDeviceSearch"
          class="absolute right-2 top-1/2 transform -translate-y-1/2 text-gray-400 hover:text-gray-600"
        >
          <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path
              stroke-linecap="round"
              stroke-linejoin="round"
              stroke-width="2"
              d="M6 18L18 6M6 6l12 12"
            ></path>
          </svg>
        </button>
      </div>
    </div>

    <!-- Canvas Controls -->
    <div class="absolute bottom-4 right-4 flex flex-col space-y-2">
      <button
        @click="toggleGrid"
        class="p-2 bg-white border border-gray-200 rounded-lg shadow-sm hover:bg-gray-50 flex-shrink-0"
        :class="{ 'bg-primary-50 border-primary-200': showGrid }"
      >
        📐
      </button>
      <button
        @click="toggleConnectionMode"
        class="p-2 bg-white border border-gray-200 rounded-lg shadow-sm hover:bg-gray-50 flex-shrink-0"
        :class="{ 'bg-green-50 border-green-200': connectionMode }"
      >
        🔗
      </button>
      <button
        @click="toggleDeviceSearch"
        class="p-2 bg-white border border-gray-200 rounded-lg shadow-sm hover:bg-gray-50 flex-shrink-0"
        :class="{ 'bg-blue-50 border-blue-200': showDeviceSearch }"
        title="Search devices"
      >
        🔍
      </button>
      <button
        @click="resetView"
        class="p-2 bg-white border border-gray-200 rounded-lg shadow-sm hover:bg-gray-50 flex-shrink-0"
      >
        🏠
      </button>
    </div>

    <!-- Save Canvas Modal -->
    <SaveCanvasModal
      ref="saveModalRef"
      :show="composableShowSaveModal"
      :device-count="deviceStore.devices.length"
      :connection-count="deviceStore.connections.length"
      @close="closeSaveModal"
      @save="handleCanvasSave"
    />

    <!-- Clear Canvas Confirmation Dialog -->
    <ConfirmDialog
      :show="composableShowClearDialog"
      title="Clear Canvas"
      message="Are you sure you want to clear the canvas? This will permanently remove all devices and connections from the current view."
      confirm-text="Clear Canvas"
      cancel-text="Cancel"
      @confirm="handleClearConfirm"
      @cancel="handleClearCancel"
    />

    <!-- Load Canvas Modal -->
    <LoadCanvasModal :show="composableShowLoadModal" @close="closeLoadModal" @load="handleCanvasLoad" />

    <!-- Load Canvas Confirmation Dialog -->
    <ConfirmDialog
      :show="showLoadConfirmDialog"
      title="Load Canvas"
      message="The current canvas is not empty. Loading a new canvas will replace all current devices and connections. Do you want to continue?"
      confirm-text="Load Canvas"
      cancel-text="Cancel"
      @confirm="handleLoadConfirm"
      @cancel="handleLoadCancel"
    />

    <!-- Duplicate Device Modal -->
    <DuplicateDeviceModal
      :show="showDuplicateDialog"
      :device-name="duplicateDeviceName"
      @cancel="handleDuplicateCancel"
      @show="handleDuplicateShow"
      @add="handleDuplicateAdd"
    />

    <!-- Shape Color Modal -->
    <ShapeColorModal
      :show="showShapeColorModal"
      :shape-id="shapeColorToEdit"
      :initial-fill-color="currentShapeColors.fill"
      :initial-stroke-color="currentShapeColors.stroke"
      :initial-stroke-width="currentShapeColors.strokeWidth"
      @close="showShapeColorModal = false"
      @save="handleShapeColorSave"
    />

    <!-- Unsaved Changes Warning Dialog -->
    <ConfirmDialog
      :show="showUnsavedChangesDialog"
      title="Unsaved Changes"
      message="You have unsaved changes that will be lost. Do you want to save your canvas before continuing?"
      confirm-text="Save Canvas"
      cancel-text="Continue Without Saving"
      @confirm="handleUnsavedChangesSave"
      @cancel="handleUnsavedChangesDiscard"
    />

    <!-- Delete Device Confirmation Dialog -->
    <ConfirmDialog
      :show="showDeleteConfirmDialog"
      title="Remove Device"
      :message="`Are you sure you want to remove '${currentDevice?.name}' from the canvas?`"
      confirm-text="Remove"
      cancel-text="Cancel"
      @confirm="confirmDeleteDevice"
      @cancel="showDeleteConfirmDialog = false"
    />

    <!-- Neighbor Discovery Result Modal -->
    <NeighborDiscoveryResultModal
      :show="showNeighborDiscoveryModal"
      :result="neighborDiscoveryResult"
      @close="closeNeighborDiscoveryModal"
    />

    <!-- Device Configuration Modal -->
    <div v-if="showConfigModal" class="fixed inset-0 z-50 overflow-y-auto" aria-labelledby="modal-title" role="dialog" aria-modal="true">
      <div class="flex items-end justify-center min-h-screen pt-4 px-4 pb-20 text-center sm:block sm:p-0">
        <div class="fixed inset-0 bg-gray-500 bg-opacity-75 transition-opacity" @click="closeConfigModal"></div>

        <!-- Modal panel -->
        <div class="inline-block align-bottom bg-white rounded-lg text-left overflow-hidden shadow-xl transform transition-all sm:my-8 sm:align-middle sm:max-w-4xl sm:w-full">
          <!-- Modal Header -->
          <div class="bg-white px-4 pt-5 pb-4 sm:p-6 sm:pb-4">
            <div class="flex items-center justify-between mb-4">
              <h3 class="text-lg leading-6 font-medium text-gray-900" id="modal-title">
                {{ configModalTitle }}
              </h3>
              <button
                @click="closeConfigModal"
                class="bg-white rounded-md text-gray-400 hover:text-gray-600 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-primary-500"
              >
                <span class="sr-only">Close</span>
                <svg class="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12" />
                </svg>
              </button>
            </div>

            <!-- Modal Content -->
            <div class="mt-3">
              <div v-if="configModalLoading" class="flex items-center justify-center py-8">
                <div class="animate-spin rounded-full h-8 w-8 border-b-2 border-primary-600"></div>
                <span class="ml-3 text-gray-600">Loading configuration...</span>
              </div>

              <div v-else>
                <!-- Error message styling -->
                <div v-if="configModalContent.startsWith('Error:')" class="bg-red-50 border border-red-200 rounded-lg p-4">
                  <div class="flex items-start">
                    <div class="flex-shrink-0">
                      <svg class="h-5 w-5 text-red-400" viewBox="0 0 20 20" fill="currentColor">
                        <path fill-rule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z" clip-rule="evenodd" />
                      </svg>
                    </div>
                    <div class="ml-3">
                      <h3 class="text-sm font-medium text-red-800">Configuration Error</h3>
                      <div class="mt-2 text-sm text-red-700">
                        <p>{{ configModalContent.replace('Error: ', '') }}</p>
                      </div>
                    </div>
                  </div>
                </div>

                <!-- Success message with CodeBlock component -->
                <div v-else>
                  <CodeBlock
                    :code="configModalContent"
                    :title="configModalTitle"
                    language="cisco"
                  />
                </div>
              </div>
            </div>
          </div>

          <!-- Modal Footer -->
          <div class="bg-gray-50 px-4 py-3 sm:px-6 sm:flex sm:flex-row-reverse">
            <button
              @click="closeConfigModal"
              type="button"
              class="w-full inline-flex justify-center rounded-md border border-transparent shadow-sm px-4 py-2 bg-primary-600 text-base font-medium text-white hover:bg-primary-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-primary-500 sm:ml-3 sm:w-auto sm:text-sm"
            >
              Close
            </button>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, computed, onMounted, onUnmounted, nextTick, watch } from 'vue'
import { useDevicesStore, type Device } from '@/stores/devices'
import { useCanvasStore } from '@/stores/canvas'
import { useShapesStore } from '@/stores/shapes'
import { type NautobotDevice, canvasApi, nautobotApi, makeAuthenticatedRequest } from '@/services/api'
import { useDeviceIcons } from '@/composables/useDeviceIcons'
import { templateService } from '@/services/templateService'
import { useCanvasControls } from '@/composables/useCanvasControls'
import { useDeviceSelection } from '@/composables/useDeviceSelection'
import { useContextMenu } from '@/composables/useContextMenu'
import { useCanvasState } from '@/composables/useCanvasState'
import { useDeviceOperations } from '@/composables/useDeviceOperations'
import { useCanvasEvents } from '@/composables/useCanvasEvents'
import { useCommands } from '@/composables/useCommands'
import { useShapeOperations } from '@/composables/useShapeOperations'
import { useNeighborDiscovery, type NeighborDiscoveryResult } from '@/composables/useNeighborDiscovery'
import SaveCanvasModal from './SaveCanvasModal.vue'
import ConfirmDialog from './ConfirmDialog.vue'
import LoadCanvasModal from './LoadCanvasModal.vue'
import DuplicateDeviceModal from './DuplicateDeviceModal.vue'
import ShapeColorModal from './ShapeColorModal.vue'
import NeighborDiscoveryResultModal from './NeighborDiscoveryResultModal.vue'
import CodeBlock from './CodeBlock.vue'

// Constants
const DEVICE_SIZE = 60
const DEVICE_HALF_SIZE = 30
const GRID_SIZE = 50
const SCALE_FACTOR = 1.1
const DEVICE_NAME_OFFSET_Y = 10
const DEVICE_TEXT_Y_OFFSET = 50

const deviceStore = useDevicesStore()
const canvasStore = useCanvasStore()
const shapesStore = useShapesStore()
const { loadDeviceIcons, getDeviceIcon: getHardcodedIcon } = useDeviceIcons()

// Map to store device-specific icons
const deviceIconMap = ref<Map<number, HTMLImageElement>>(new Map())

// Enhanced icon getter that uses templates first, then falls back to hardcoded icons
const getDeviceIcon = (device: Device): HTMLImageElement | null => {
  // Check if we have a cached icon for this device
  if (deviceIconMap.value.has(device.id)) {
    return deviceIconMap.value.get(device.id)!
  }

  // Fall back to hardcoded icon immediately for rendering
  return getHardcodedIcon(device.device_type)
}

// Async function to load device icon from templates
const loadDeviceIconFromTemplate = async (device: Device) => {
  try {
    // Parse device properties to get platform and device type info
    const props = device.properties ? JSON.parse(device.properties) : {}
    const platformId = props.platform_id
    const deviceTypeModel = props.device_type_model
    console.log('🔍 Loading icon for device:', device.name, {
      deviceId: device.id,
      rawProperties: device.properties,
      parsedProperties: props,
      platformId,
      deviceTypeModel,
      allKeys: Object.keys(props)
    })

    // Try to get icon from template service
    const templateIcon = await templateService.getDeviceIcon(platformId, deviceTypeModel)
    if (templateIcon) {
      console.log('✅ Using template icon for device:', device.name)
      // Create new Map to trigger reactivity
      deviceIconMap.value = new Map(deviceIconMap.value).set(device.id, templateIcon)
      console.log('🔄 Icon map updated, map size:', deviceIconMap.value.size)
      return
    }

    // Use hardcoded icon as fallback
    const fallbackIcon = getHardcodedIcon(device.device_type)
    if (fallbackIcon) {
      deviceIconMap.value = new Map(deviceIconMap.value).set(device.id, fallbackIcon)
    }
  } catch (error) {
    console.error('Error loading device icon:', error)
  }
}

// Watch for device changes and load template icons
watch(() => deviceStore.devices, async (devices) => {
  for (const device of devices) {
    if (!deviceIconMap.value.has(device.id)) {
      await loadDeviceIconFromTemplate(device)
    }
  }
}, { deep: true, immediate: true })

// Initialize canvas controls composable
const canvasControls = useCanvasControls()
const { 
  showGrid: gridEnabled,
  connectionMode: connectionModeEnabled,
  resetView,
  fitToScreen,
  toggleGrid,
  toggleConnectionMode,
} = canvasControls

// Initialize context menu composable
const contextMenuComposable = useContextMenu()
const {
  contextMenu,
  contextMenuShownAt,
  showContextMenu,
  hideContextMenu,
} = contextMenuComposable

// Initialize device selection composable
const deviceSelectionComposable = useDeviceSelection()
const {
  selectedDevices: composableSelectedDevices,
  selectedDevice: composableSelectedDevice,
  selectDevicesInBox: composableSelectDevicesInBox,
  selectDevice: composableSelectDevice,
  clearSelection: composableClearSelection,
} = deviceSelectionComposable

// Use the composable versions as the primary references
const selectedDevices = composableSelectedDevices

// Initialize device operations composable
const deviceOperationsComposable = useDeviceOperations()
const {
  deleteDevice: composableDeleteDevice,
  editDevice: composableEditDevice,
  showDeleteConfirmDialog,
  currentDevice,
  confirmDeleteDevice,
} = deviceOperationsComposable

// Initialize canvas events composable
const canvasEventsComposable = useCanvasEvents()
const {
  onGlobalMouseUp,
  onDeviceMouseDown: composableOnDeviceMouseDown,
  onDeviceClick: composableOnDeviceClick,
  onDeviceDoubleClick: composableOnDeviceDoubleClick,
  onRightClick: composableOnRightClick,
} = canvasEventsComposable

// Initialize canvas state composable
const canvasStateComposable = useCanvasState()
const {
  currentCanvasId: composableCanvasId,
  hasUnsavedChanges: composableHasUnsavedChanges,
  showSaveModal: composableShowSaveModal,
  showLoadModal: composableShowLoadModal,
  showClearDialog: composableShowClearDialog,
  showUnsavedChangesDialog,
  pendingAction,
  quickSave: composableQuickSave,
  clearCanvas: composableClearCanvas,
  executeClearCanvas,
  promptToSaveBeforeAction,
  updateSavedState,
  saveCanvasData,
  loadCanvasById: composableLoadCanvasById,
} = canvasStateComposable

const canvasContainer = ref<HTMLElement>()
const stage = ref()

// Canvas state
const canvasSize = reactive({ width: 0, height: 0 })
// Use canvas store for scale and position
const scale = computed(() => canvasStore.scale)
const position = computed(() => canvasStore.position)
// Use composable state for grid and connection mode instead of local refs
const showGrid = gridEnabled
const connectionMode = connectionModeEnabled
const selectedDevice = composableSelectedDevice  // Use composable version
const isDragOver = ref(false)

// Selection state
const selectionBox = ref<{
  startX: number
  startY: number
  endX: number
  endY: number
} | null>(null)

// Selected devices - now handled by useDeviceSelection composable

// Function to select devices within a selection box - now handled by composable
const selectDevicesInBox = composableSelectDevicesInBox

// Context menu state - now handled by useContextMenu composable

// Flag to track device right-clicks to prevent canvas menu override
const deviceRightClickInProgress = ref(false)

// Flag to track connection right-clicks to prevent canvas menu override
const connectionRightClickInProgress = ref(false)

// Connection state
const connectionStart = ref<{
  device: Device
  point: { x: number; y: number }
} | null>(null)

// Selected connection state
const selectedConnection = ref<number | null>(null)

// Initialize shape operations composable
const shapeOperationsComposable = useShapeOperations()
const {
  selectedShape,
  selectedShapes,
  transformer,
  showShapeColorModal,
  shapeColorToEdit,
  currentShapeColors,
  onShapeClick,
  onShapeDragEnd,
  onShapeRightClick: composableOnShapeRightClick,
  openShapeColorModal,
  handleShapeColorSave,
  deleteShape,
  deleteMultiShapes,
  alignShapesHorizontally,
  alignShapesVertically,
  clearShapeSelection,
} = shapeOperationsComposable

// Watch for transformer changes to update shape size
watch(transformer, () => {
  if (transformer.value) {
    const tr = transformer.value.getNode()
    tr.on('transformend', async () => {
      const nodes = tr.nodes()
      if (nodes.length > 0 && selectedShape.value) {
        const groupNode = nodes[0]
        const scaleX = groupNode.scaleX()
        const scaleY = groupNode.scaleY()

        // Get the shape data to calculate new dimensions
        const shape = shapesStore.shapes.find((s) => s.id === selectedShape.value)
        if (shape) {
          const newWidth = shape.width * scaleX
          const newHeight = shape.height * scaleY

          shapesStore.updateShape(selectedShape.value, {
            width: newWidth,
            height: newHeight,
          })

          // Reset scale after updating dimensions
          groupNode.scaleX(1)
          groupNode.scaleY(1)
        }
      }
    })
  }
})

// Initialize commands composable
const commandsComposable = useCommands()
const {
  commands: availableCommands,
  commandsLoading,
  commandsError,
  getCommandsForPlatform,
  getDevicePlatform,
  reloadCommands,
} = commandsComposable

// Initialize neighbor discovery composable
const neighborDiscoveryComposable = useNeighborDiscovery()
const {
  addCdpNeighbors,
  addMacNeighbors,
  addStaticNeighbors,
  addOspfNeighbors,
  addBgpNeighbors,
} = neighborDiscoveryComposable

// Neighbor Discovery Modal state
const showNeighborDiscoveryModal = ref(false)
const neighborDiscoveryResult = ref<NeighborDiscoveryResult | null>(null)

const handleNeighborDiscovery = async (device: Device, discoveryFn: (device: Device) => Promise<NeighborDiscoveryResult | null>) => {
  hideContextMenu()
  
  const result = await discoveryFn(device)
  
  if (result) {
    if (result.error) {
      alert(`Error: ${result.error}`)
    } else {
      neighborDiscoveryResult.value = result
      showNeighborDiscoveryModal.value = true
    }
  }
}

const closeNeighborDiscoveryModal = () => {
  showNeighborDiscoveryModal.value = false
  neighborDiscoveryResult.value = null
}


// Execute a command on a device
const executeCommand = async (device: Device, command: any) => {
  console.log(`🚀 Executing command on ${device.name} (${command.platform}):`)
  console.log(`Command: ${command.command}`)
  console.log(`Parser: ${command.parser}`)

  hideContextMenu()

  // Show command execution modal
  await showCommandExecution(device, command)
}

// Save Canvas Modal state
const saveModalRef = ref()

// Load Canvas Modal state - composable version used

// Load Canvas Confirmation state
const showLoadConfirmDialog = ref(false)
const pendingCanvasId = ref<number | null>(null)

// Duplicate Device Modal state
const showDuplicateDialog = ref(false)
const duplicateDeviceName = ref('')
const pendingDeviceData = ref<any>(null)
const duplicateExistingDevice = ref<Device | null>(null)

// Device Configuration Modal state
// Device Configuration Modal state (using local implementations, not composable)
const showConfigModal = ref(false)
const configModalTitle = ref('')
const configModalContent = ref('')
const configModalLoading = ref(false)
const currentConfigDevice = ref<Device | null>(null)

// Device Search state
const showDeviceSearch = ref(false)
const deviceSearchQuery = ref('')
const deviceSearchInput = ref<HTMLInputElement>()

// Mouse state
const mouseState = reactive({
  isDown: false,
  startX: 0,
  startY: 0,
  isDragging: false,
})

// Grid lines computation
const gridLines = computed(() => {
  const gridSize = GRID_SIZE
  const lines = { vertical: [], horizontal: [] } as any

  // Vertical lines
  for (let i = 0; i <= canvasSize.width; i += gridSize) {
    lines.vertical.push([i, 0, i, canvasSize.height])
  }

  // Horizontal lines
  for (let i = 0; i <= canvasSize.height; i += gridSize) {
    lines.horizontal.push([0, i, canvasSize.width, i])
  }

  return lines
})

// Render connections
const renderConnections = computed(() => {
  return deviceStore.connections
    .map((connection) => {
      const sourceDevice = deviceStore.devices.find((d) => d.id === connection.source_device_id)
      const targetDevice = deviceStore.devices.find((d) => d.id === connection.target_device_id)

      if (!sourceDevice || !targetDevice) return null

      // Use drag positions if device is being dragged, otherwise use stored positions
      const sourcePos = dragPositions.value.get(sourceDevice.id) || {
        x: sourceDevice.position_x,
        y: sourceDevice.position_y
      }
      const targetPos = dragPositions.value.get(targetDevice.id) || {
        x: targetDevice.position_x,
        y: targetDevice.position_y
      }

      return {
        id: connection.id,
        points: [
          sourcePos.x + DEVICE_HALF_SIZE,
          sourcePos.y + DEVICE_HALF_SIZE,
          targetPos.x + DEVICE_HALF_SIZE,
          targetPos.y + DEVICE_HALF_SIZE,
        ],
      }
    })
    .filter((connection): connection is NonNullable<typeof connection> => connection !== null)
})

// Context menu items
const contextMenuItems = computed(() => {
  console.log('🔵 DEBUG: contextMenuItems computed, targetType:', contextMenu.targetType, 'target:', contextMenu.target)

  // Shape context menu
  if (contextMenu.targetType === 'shape') {
    console.log('🔵 DEBUG: Building shape context menu')
    const items = [
      { icon: '🎨', label: 'Color', action: () => { hideContextMenu(); openShapeColorModal(contextMenu.target as any) } },
      {
        icon: '📐',
        label: 'Alignment',
        submenu: [
          { icon: '↔️', label: 'Horizontal', action: () => { hideContextMenu(); alignShapesHorizontally() } },
          { icon: '↕️', label: 'Vertical', action: () => { hideContextMenu(); alignShapesVertically() } },
        ],
      },
      { icon: '─', label: '─────────', action: () => {}, separator: true },
      { icon: '🗑️', label: 'Remove', action: () => { hideContextMenu(); deleteShape(contextMenu.target as any) } },
    ]
    console.log('🔵 DEBUG: Shape context menu items:', items)
    return items
  }

  // Multi-shape context menu
  if (contextMenu.targetType === 'multi-shape') {
    console.log('🔵 DEBUG: Building multi-shape context menu')
    const selectedCount = selectedShapes.value.size
    const items = [
      {
        icon: '📐',
        label: 'Alignment',
        submenu: [
          { icon: '↔️', label: 'Horizontal', action: () => { hideContextMenu(); alignShapesHorizontally() } },
          { icon: '↕️', label: 'Vertical', action: () => { hideContextMenu(); alignShapesVertically() } },
        ],
      },
      { icon: '─', label: '─────────', action: () => {}, separator: true },
      { icon: '🗑️', label: `Remove ${selectedCount} shapes`, action: () => { hideContextMenu(); deleteMultiShapes() } },
    ]
    console.log('🔵 DEBUG: Multi-shape context menu items:', items)
    return items
  }

  // Connection context menu
  if (contextMenu.targetType === 'connection') {
    const items = [
      { icon: '👁️', label: 'Show', action: () => { hideContextMenu(); showConnectionInfo(contextMenu.target as any) } },
      { icon: '📊', label: 'Status', action: () => { hideContextMenu(); showConnectionStatus(contextMenu.target as any) } },
      { icon: '📈', label: 'Stats', action: () => { hideContextMenu(); showConnectionStats(contextMenu.target as any) } },
      { icon: '─', label: '─────────', action: () => {}, separator: true },
      { icon: '🗑️', label: 'Delete', action: () => { hideContextMenu(); deleteConnection(contextMenu.target as any) } },
    ]
    return items
  }

  if (!contextMenu.target) {
    if (contextMenu.targetType === 'canvas') {
      const items = [
        { icon: '🖼️', label: 'Fit to Screen', action: () => { hideContextMenu(); fitToScreen(canvasContainer.value || null) } },
        { icon: '🏠', label: 'Reset View', action: () => { hideContextMenu(); resetView() } },
        {
          icon: '🎨',
          label: 'Canvas',
          submenu: [
            { icon: '📂', label: 'Load', action: () => { hideContextMenu(); loadCanvas() } },
            { icon: '💾', label: 'Save', action: () => { hideContextMenu(); saveCanvas() } },
            { icon: '📋', label: 'Save As', action: () => { hideContextMenu(); saveCanvasAs() } },
            { icon: '🗑️', label: 'Clear', action: () => { hideContextMenu(); clearCanvas() } },
          ],
        },
      ]
      return items
    }
    return []
  }

  // Multi-device context menu
  if (contextMenu.targetType === 'multi-device') {
    const selectedCount = selectedDevices.value.size
    const items = [
      {
        icon: '📊',
        label: `Overview (${selectedCount} devices)`,
        action: () => { hideContextMenu(); showMultiDeviceOverview() }
      },
      {
        icon: '⚙️',
        label: 'Config',
        submenu: [
          { icon: '👁️', label: 'Show All', action: () => { hideContextMenu(); showMultiDeviceConfig() } },
          { icon: '📝', label: 'Show All Changes', action: () => { hideContextMenu(); showMultiDeviceChanges() } },
        ],
      },
      { icon: '💻', label: 'Commands', action: () => { hideContextMenu(); showMultiDeviceCommands() } },
      {
        icon: '🔗',
        label: 'Neighbors',
        submenu: [
          { icon: '👁️', label: 'Show All', action: () => { hideContextMenu(); showMultiDeviceNeighbors() } },
          { icon: '➕', label: 'Add', action: () => { hideContextMenu(); addMultiDeviceNeighborsToCanvas() } },
          {
            icon: '🔗',
            label: 'Connect to',
            action: selectedCount === 2
              ? () => { hideContextMenu(); connectTwoDevices() }
              : () => {},
            disabled: selectedCount !== 2
          },
        ],
      },
      { icon: '🔍', label: 'Analyze All', action: () => { hideContextMenu(); analyzeMultiDevices() } },
      { icon: '─', label: '─────────', action: () => {}, separator: true },
      {
        icon: '📐',
        label: 'Alignment',
        submenu: [
          { icon: '↔️', label: 'Horizontal', action: () => { alignDevicesHorizontally() } },
          { icon: '↕️', label: 'Vertical', action: () => { alignDevicesVertically() } },
        ],
      },
      {
        icon: '🗑️',
        label: `Remove ${selectedCount} devices`,
        action: () => { hideContextMenu(); deleteMultiDevices() }
      },
    ]
    return items
  }

  // Single device context menu
  const device = contextMenu.target!
  const devicePlatform = getDevicePlatform(device.properties)
  const platformCommands = getCommandsForPlatform(devicePlatform)
  
  // Build Commands submenu with Send and Reload
  const sendSubmenu = platformCommands.length > 0
    ? platformCommands.map(command => ({
        icon: '⚡',
        label: command.display || command.command,
        action: () => { hideContextMenu(); executeCommand(device, command) }
      }))
    : [{ 
        icon: '❌', 
        label: devicePlatform ? `No commands for ${devicePlatform}` : 'No platform detected',
        action: () => { 
          hideContextMenu()
          console.log(`No commands configured for platform: ${devicePlatform || 'unknown'}`)
        }
      }]
  
  const commandsSubmenu = [
    {
      icon: '📤',
      label: 'Send',
      submenu: sendSubmenu
    },
    {
      icon: '🔄',
      label: 'Reload',
      action: async () => { 
        hideContextMenu()
        console.log('🔄 Reloading commands...')
        await reloadCommands()
        console.log('✅ Commands reloaded successfully')
      }
    }
  ]
  
  const items = [
    { icon: '📊', label: 'Overview', action: () => { hideContextMenu(); showDeviceOverview(contextMenu.target!) } },
    {
      icon: '⚙️',
      label: 'Config',
      submenu: [
        {
          icon: '👁️',
          label: 'Show',
          submenu: [
            { icon: '🔧', label: 'Running', action: () => { hideContextMenu(); showDeviceRunningConfig(contextMenu.target!) } },
            { icon: '💾', label: 'Startup', action: () => { hideContextMenu(); showDeviceStartupConfig(contextMenu.target!) } },
          ]
        },
        { icon: '📝', label: 'Show Changes', action: () => { hideContextMenu(); showDeviceChanges(contextMenu.target!) } },
      ],
    },
    {
      icon: '💻',
      label: 'Commands',
      submenu: commandsSubmenu
    },
    {
      icon: '🔗',
      label: 'Neighbors',
      submenu: [
        { icon: '👁️', label: 'Show', action: () => { hideContextMenu(); showNeighbors(contextMenu.target!) } },
        {
          icon: '➕',
          label: 'Add',
          submenu: [
            {
              icon: '🔗',
              label: 'Layer2',
              submenu: [
                { icon: '📡', label: 'CDP', action: () => handleNeighborDiscovery(contextMenu.target!, addCdpNeighbors) },
                { icon: '🔗', label: 'MAC', action: () => { hideContextMenu(); addMacNeighbors(contextMenu.target!) } },
              ]
            },
            {
              icon: '🌐',
              label: 'Layer3',
              submenu: [
                { icon: '📌', label: 'Static', action: () => { hideContextMenu(); addStaticNeighbors(contextMenu.target!) } },
                { icon: '🔀', label: 'OSPF', action: () => handleNeighborDiscovery(contextMenu.target!, addOspfNeighbors) },
                { icon: '🌍', label: 'BGP', action: () => { hideContextMenu(); addBgpNeighbors(contextMenu.target!) } },
              ]
            },
          ]
        },
        {
          icon: '🔗',
          label: 'Connect',
          action: selectedDevices.value.size === 2
            ? () => { hideContextMenu(); connectTwoDevices() }
            : () => {},
          disabled: selectedDevices.value.size !== 2
        },
      ],
    },
    { icon: '🔍', label: 'Analyze', action: () => { hideContextMenu(); analyzeDevice(contextMenu.target!) } },
    { icon: '─', label: '─────────', action: () => {}, separator: true },
    {
      icon: '📐',
      label: 'Alignment',
      submenu: [
        { icon: '↔️', label: 'Horizontal', action: () => { alignDevicesHorizontally() } },
        { icon: '↕️', label: 'Vertical', action: () => { alignDevicesVertically() } },
      ],
    },
    { icon: '🗑️', label: 'Remove', action: () => { hideContextMenu(); deleteDevice(contextMenu.target!) } },
  ]
  return items
})

// Device helpers

const getDeviceColor = (type: string) => {
  const colors = {
    router: '#dbeafe',
    switch: '#dcfce7',
    firewall: '#fef3c7',
    vpn_gateway: '#e0e7ff',
  }
  return colors[type as keyof typeof colors] || '#f3f4f6'
}

// Context menu functions
const loadCanvas = () => {
  promptToSaveBeforeAction('loading a canvas', () => {
    composableShowLoadModal.value = true
  })
}

// Load Canvas Modal functions
const closeLoadModal = () => {
  composableShowLoadModal.value = false
}

const handleCanvasLoad = (canvasId: number) => {

  // Check if current canvas has devices
  if (deviceStore.devices.length > 0) {
    // Show confirmation dialog
    pendingCanvasId.value = canvasId
    composableShowLoadModal.value = false
    showLoadConfirmDialog.value = true
  } else {
    // Load directly if canvas is empty
    loadCanvasById(canvasId)
  }
}

const handleLoadConfirm = () => {
  showLoadConfirmDialog.value = false
  if (pendingCanvasId.value) {
    loadCanvasById(pendingCanvasId.value)
    pendingCanvasId.value = null
  }
}

const handleLoadCancel = () => {
  showLoadConfirmDialog.value = false
  pendingCanvasId.value = null
  // Reopen the load modal
  composableShowLoadModal.value = true
}

const loadCanvasById = async (canvasId: number) => {
  try {
    // Use the composable's loadCanvasById which includes shapes
    await composableLoadCanvasById(canvasId)

    // Close the load modal after successful loading
    composableShowLoadModal.value = false
  } catch (error) {
    console.error('❌ Failed to load canvas:', error)
    // notificationStore.showError('Failed to load canvas')
  }
}

// Quick save to current canvas - now handled by useCanvasState composable
const saveCanvas = composableQuickSave

// Save As - now handled by useCanvasState composable
const saveCanvasAs = () => {
  composableShowSaveModal.value = true
}

// Clear canvas - now handled by useCanvasState composable
const clearCanvas = composableClearCanvas

// Clear Canvas Confirmation Dialog functions
const handleClearConfirm = () => {
  composableShowClearDialog.value = false
  executeClearCanvas()
}

const handleClearCancel = () => {
  composableShowClearDialog.value = false
}

// Save Canvas Modal functions
const closeSaveModal = () => {
  composableShowSaveModal.value = false
}

const handleCanvasSave = async (data: { name: string; sharable: boolean; canvasId?: number }) => {
  try {
    // Use the composable's saveCanvasData function which includes shapes
    await saveCanvasData(data)

    composableShowSaveModal.value = false

    // Execute pending action if there was one (from unsaved changes dialog)
    if (pendingAction.value) {
      pendingAction.value()
      pendingAction.value = null
    }

    // TODO: Show success notification
    // notificationStore.showSuccess(`Canvas "${data.name}" ${data.canvasId ? 'updated' : 'saved'} successfully`)
  } catch (error) {
    console.error('❌ Failed to save canvas:', error)

    // Show error to user via modal
    if (saveModalRef.value) {
      saveModalRef.value.setError(error instanceof Error ? error.message : 'Failed to save canvas')
      saveModalRef.value.setSaving(false)
    }
  }
}

// Duplicate Device Modal functions
const handleDuplicateCancel = () => {
  showDuplicateDialog.value = false
  pendingDeviceData.value = null
  duplicateExistingDevice.value = null
  duplicateDeviceName.value = ''
}

const handleDuplicateShow = () => {
  if (duplicateExistingDevice.value) {
    // Center and highlight the existing device
    centerOnDevice(duplicateExistingDevice.value)
    // Clear selection and select the existing device
    selectedDevices.value.clear()
    selectedDevice.value = duplicateExistingDevice.value
  }
  handleDuplicateCancel()
}

const handleDuplicateAdd = () => {
  if (pendingDeviceData.value) {
    try {
      deviceStore.createDevice(pendingDeviceData.value)
    } catch (error) {
      console.error('❌ Failed to create duplicate device:', error)
    }
  }
  handleDuplicateCancel()
}

const showDeviceOverview = (device: Device) => {
}

// Device configuration functions
const showDeviceRunningConfig = async (device: Device) => {
  await showDeviceConfiguration(device, 'running-config', 'Running Configuration')
}

const showDeviceStartupConfig = async (device: Device) => {
  await showDeviceConfiguration(device, 'startup-config', 'Startup Configuration')
}

const showDeviceConfiguration = async (device: Device, configType: string, title: string) => {
  try {
    // Set modal state
    currentConfigDevice.value = device
    configModalTitle.value = `${title} - ${device.name}`
    configModalContent.value = ''
    configModalLoading.value = true
    showConfigModal.value = true

    // Get nautobot_id from device properties
    const deviceProps = device.properties ? JSON.parse(device.properties) : {}
    const nautobotId = deviceProps.nautobot_id

    if (!nautobotId) {
      configModalContent.value = 'Error: Device does not have a Nautobot ID'
      return
    }

    // Make API call to get configuration
    const response = await makeAuthenticatedRequest(`/api/devices/${nautobotId}/${configType}`)

    if (response.ok) {
      const data = await response.json()

      if (data.success) {
        configModalContent.value = data.output || 'No configuration data received'
      } else {
        // Handle specific error types from backend
        const errorType = data.error_type
        let errorMessage = data.error || 'Failed to retrieve configuration'

        if (errorType === 'no_credentials') {
          errorMessage = 'No valid credentials found. Please add TACACS or SSH credentials in Settings.'
        } else if (errorType === 'authentication_failed') {
          errorMessage = 'Login failed. Please check your credentials in Settings.'
        } else if (errorType === 'timeout') {
          errorMessage = 'Connection timeout. Please check network connectivity to the device.'
        }

        configModalContent.value = `Error: ${errorMessage}`
      }
    } else {
      const errorData = await response.json()
      configModalContent.value = `Error: ${errorData.detail || 'Failed to retrieve configuration'}`
    }
  } catch (error) {
    console.error(`Error fetching ${configType}:`, error)
    configModalContent.value = `Error: ${error instanceof Error ? error.message : 'Unknown error occurred'}`
  } finally {
    configModalLoading.value = false
  }
}

const closeConfigModal = () => {
  showConfigModal.value = false
  currentConfigDevice.value = null
  configModalContent.value = ''
  configModalTitle.value = ''
}

// Command execution modal
const showCommandExecution = async (device: Device, command: any) => {
  // Set modal state
  currentConfigDevice.value = device
  configModalTitle.value = `Command Execution - ${device.name}`
  configModalContent.value = ''
  configModalLoading.value = true
  showConfigModal.value = true

  // Get nautobot_id from device properties
  const deviceProps = device.properties ? JSON.parse(device.properties) : {}
  const nautobotId = deviceProps.nautobot_id

  if (!nautobotId) {
    configModalLoading.value = false
    configModalContent.value = 'Error: Device does not have a Nautobot ID'
    return
  }

  try {
    const response = await fetch(`/api/devices/${nautobotId}/send/${command.id}`, {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${localStorage.getItem('token')}`,
        'Content-Type': 'application/json',
      },
    })

    if (response.ok) {
      const data = await response.json()
      if (data.success) {
        // Format the output based on whether it was parsed or not
        let formattedOutput = ''

        if (data.parsed && data.parser_used) {
          // For parsed output, display JSON formatted
          if (typeof data.output === 'object') {
            formattedOutput = `Command: ${data.command}\nParser: ${data.parser_used}\nExecution Time: ${data.execution_time?.toFixed(2) || 'N/A'}s\n\n--- Parsed Output (${data.parser_used}) ---\n${JSON.stringify(data.output, null, 2)}`
          } else {
            formattedOutput = `Command: ${data.command}\nParser: ${data.parser_used}\nExecution Time: ${data.execution_time?.toFixed(2) || 'N/A'}s\n\n--- Parsed Output (${data.parser_used}) ---\n${data.output}`
          }
        } else {
          // For raw output, display as text
          formattedOutput = `Command: ${data.command}\nExecution Time: ${data.execution_time?.toFixed(2) || 'N/A'}s\n\n--- Raw Output ---\n${data.output || 'No output received'}`
        }

        configModalContent.value = formattedOutput
      } else {
        // Handle specific error types from backend
        const errorType = data.error_type
        let errorMessage = data.error || 'Unknown error occurred'

        if (errorType === 'authentication_failed') {
          errorMessage = 'Authentication failed. Please check your credentials in Settings.'
        } else if (errorType === 'no_credentials') {
          errorMessage = 'No credentials found. Please add TACACS or SSH credentials in Settings.'
        } else if (errorType === 'timeout') {
          errorMessage = 'Connection timeout. The device did not respond in time.'
        }

        configModalContent.value = `Error: ${errorMessage}`
      }
    } else {
      const errorData = await response.json()
      configModalContent.value = `Error: ${errorData.detail || 'Failed to execute command'}`
    }
  } catch (error) {
    console.error('Error executing command:', error)
    configModalContent.value = `Error: ${error instanceof Error ? error.message : 'Unknown error occurred'}`
  } finally {
    configModalLoading.value = false
  }
}

const showDeviceChanges = (device: Device) => {
}

const showDeviceCommands = (device: Device) => {
}

const showDeviceNeighbors = (device: Device) => {
}

// Show neighbors using CDP/LLDP
const showNeighbors = async (device: Device) => {
  try {
    // Set modal state
    currentConfigDevice.value = device
    configModalTitle.value = `CDP Neighbors - ${device.name}`
    configModalContent.value = ''
    configModalLoading.value = true
    showConfigModal.value = true

    // Get nautobot_id from device properties
    const deviceProps = device.properties ? JSON.parse(device.properties) : {}
    const nautobotId = deviceProps.nautobot_id

    if (!nautobotId) {
      configModalLoading.value = false
      configModalContent.value = 'Error: Device does not have a Nautobot ID'
      return
    }

    // Make API call to get CDP neighbors
    const response = await makeAuthenticatedRequest(`/api/devices/${nautobotId}/cdp-neighbors`)

    if (response.ok) {
      const data = await response.json()

      if (data.success) {
        // Format the output
        if (typeof data.output === 'object') {
          configModalContent.value = `Command: ${data.command || 'show cdp neighbors'}\nExecution Time: ${data.execution_time?.toFixed(2) || 'N/A'}s\n\n--- CDP Neighbors ---\n${JSON.stringify(data.output, null, 2)}`
        } else {
          configModalContent.value = `Command: ${data.command || 'show cdp neighbors'}\nExecution Time: ${data.execution_time?.toFixed(2) || 'N/A'}s\n\n--- CDP Neighbors ---\n${data.output || 'No neighbors found'}`
        }
      } else {
        // Handle specific error types from backend
        const errorType = data.error_type
        let errorMessage = data.error || 'Failed to retrieve neighbors'

        if (errorType === 'authentication_failed') {
          errorMessage = 'Authentication failed. Please check your credentials in Settings.'
        } else if (errorType === 'no_credentials') {
          errorMessage = 'No credentials found. Please add TACACS or SSH credentials in Settings.'
        } else if (errorType === 'timeout') {
          errorMessage = 'Connection timeout. The device did not respond in time.'
        }

        configModalContent.value = `Error: ${errorMessage}`
      }
    } else {
      const errorData = await response.json()
      configModalContent.value = `Error: ${errorData.detail || 'Failed to retrieve neighbors'}`
    }
  } catch (error) {
    console.error('Error fetching CDP neighbors:', error)
    configModalContent.value = `Error: ${error instanceof Error ? error.message : 'Unknown error occurred'}`
  } finally {
    configModalLoading.value = false
  }
}

// Connect two selected devices with a line
const connectTwoDevices = () => {
  if (selectedDevices.value.size !== 2) {
    console.error('❌ Exactly 2 devices must be selected to connect them')
    return
  }

  const deviceIds = Array.from(selectedDevices.value)
  const device1 = deviceStore.devices.find(d => d.id === deviceIds[0])
  const device2 = deviceStore.devices.find(d => d.id === deviceIds[1])

  if (!device1 || !device2) {
    console.error('❌ Could not find selected devices')
    return
  }

  try {
    console.log(`🔗 Creating connection between ${device1.name} and ${device2.name}`)
    deviceStore.createConnection({
      source_device_id: device1.id,
      target_device_id: device2.id,
      connection_type: 'ethernet',
    })
    console.log('✅ Connection created successfully')
  } catch (error) {
    console.error('❌ Failed to create connection:', error)
  }
}

const analyzeDevice = (device: Device) => {
}

// Alignment functions
const alignDevicesHorizontally = () => {
  if (!contextMenu.target) return
  
  // Get all selected devices or just the target device
  const devicesToAlign = selectedDevices.value.size > 1 
    ? Array.from(selectedDevices.value)
        .map(id => deviceStore.devices.find(d => d.id === id))
        .filter((device): device is Device => device !== undefined)
    : [contextMenu.target]
    
  if (devicesToAlign.length < 2) return
  
  // Use the y-position of the target device as the alignment line
  const alignmentY = contextMenu.target.position_y
  
  // Update all devices to have the same y position
  devicesToAlign.forEach(device => {
    if (device.id !== contextMenu.target?.id) {
      deviceStore.updateDevice(device.id, {
        position_y: alignmentY
      })
    }
  })
  
  hideContextMenu()
}

const alignDevicesVertically = () => {
  if (!contextMenu.target) return
  
  // Get all selected devices or just the target device
  const devicesToAlign = selectedDevices.value.size > 1 
    ? Array.from(selectedDevices.value)
        .map(id => deviceStore.devices.find(d => d.id === id))
        .filter((device): device is Device => device !== undefined)
    : [contextMenu.target]
    
  if (devicesToAlign.length < 2) return
  
  // Use the x-position of the target device as the alignment line
  const alignmentX = contextMenu.target.position_x
  
  // Update all devices to have the same x position
  devicesToAlign.forEach(device => {
    if (device.id !== contextMenu.target?.id) {
      deviceStore.updateDevice(device.id, {
        position_x: alignmentX
      })
    }
  })
  
  hideContextMenu()
}

// Multi-device action functions
const showMultiDeviceOverview = () => {
  const selectedDevicesArray = Array.from(selectedDevices.value)
    .map(id => deviceStore.devices.find(d => d.id === id))
    .filter((device): device is Device => device !== undefined)
  
  hideContextMenu()
}

const showMultiDeviceConfig = () => {
  const selectedDevicesArray = Array.from(selectedDevices.value)
    .map(id => deviceStore.devices.find(d => d.id === id))
    .filter((device): device is Device => device !== undefined)
  
  hideContextMenu()
}

const showMultiDeviceChanges = () => {
  const selectedDevicesArray = Array.from(selectedDevices.value)
    .map(id => deviceStore.devices.find(d => d.id === id))
    .filter((device): device is Device => device !== undefined)
  
  hideContextMenu()
}

const showMultiDeviceCommands = () => {
  const selectedDevicesArray = Array.from(selectedDevices.value)
    .map(id => deviceStore.devices.find(d => d.id === id))
    .filter((device): device is Device => device !== undefined)
  
  hideContextMenu()
}

const showMultiDeviceNeighbors = () => {
  const selectedDevicesArray = Array.from(selectedDevices.value)
    .map(id => deviceStore.devices.find(d => d.id === id))
    .filter((device): device is Device => device !== undefined)

  console.log('👁️ Show neighbors for multiple devices:', selectedDevicesArray.map(d => d.name))
  // TODO: Implement showing neighbors for multiple devices
  hideContextMenu()
}

const addMultiDeviceNeighborsToCanvas = () => {
  const selectedDevicesArray = Array.from(selectedDevices.value)
    .map(id => deviceStore.devices.find(d => d.id === id))
    .filter((device): device is Device => device !== undefined)

  console.log('➕ Add neighbors to canvas for multiple devices:', selectedDevicesArray.map(d => d.name))
  // TODO: Implement adding neighbors to canvas for multiple devices
  alert('Add neighbors to canvas for multiple devices feature coming soon!')
  hideContextMenu()
}

const analyzeMultiDevices = () => {
  const selectedDevicesArray = Array.from(selectedDevices.value)
    .map(id => deviceStore.devices.find(d => d.id === id))
    .filter((device): device is Device => device !== undefined)
  
  hideContextMenu()
}

const deleteMultiDevices = () => {
  const selectedDevicesArray = Array.from(selectedDevices.value)
    .map(id => deviceStore.devices.find(d => d.id === id))
    .filter((device): device is Device => device !== undefined)

  const deviceNames = selectedDevicesArray.map(d => d.name).join(', ')

  if (confirm(`Are you sure you want to remove ${selectedDevicesArray.length} devices from the canvas?\n\nDevices: ${deviceNames}`)) {
    try {
      let successCount = 0
      const deviceIds = [...selectedDevices.value] // Copy the set to iterate safely
      
      for (const deviceId of deviceIds) {
        const success = deviceStore.deleteDevice(deviceId)
        if (success) {
          successCount++
        }
      }

      // Clear selections after deletion
      selectedDevices.value.clear()
      selectedDevice.value = null
      deviceStore.setSelectedDevice(null)

    } catch (error) {
      console.error('❌ Failed to delete multiple devices:', error)
    }
  } else {
  }

  hideContextMenu()
}

// eslint-disable-next-line @typescript-eslint/no-unused-vars
const getConnectionPoints = (device: Device) => {
  return [
    { x: 0, y: DEVICE_HALF_SIZE }, // Left (middle of device height)
    { x: DEVICE_SIZE, y: DEVICE_HALF_SIZE }, // Right (middle of device height)
    { x: DEVICE_HALF_SIZE, y: 0 }, // Top (middle of device width)
    { x: DEVICE_HALF_SIZE, y: DEVICE_SIZE }, // Bottom (middle of device width)
  ]
}

// Helper function to map Nautobot device types to canvas device types
const mapNautobotDeviceType = (nautobotDevice: NautobotDevice): Device['device_type'] => {
  const role = nautobotDevice.role?.name?.toLowerCase() || ''
  const deviceType = nautobotDevice.device_type?.model?.toLowerCase() || ''

  // Map based on role first, then device type
  if (role.includes('router') || deviceType.includes('router')) {
    return 'router'
  }
  if (role.includes('switch') || deviceType.includes('switch')) {
    return 'switch'
  }
  if (role.includes('firewall') || deviceType.includes('firewall')) {
    return 'firewall'
  }
  if (role.includes('vpn') || deviceType.includes('vpn')) {
    return 'vpn_gateway'
  }

  // Default to router for network devices
  return 'router'
}

// Event handlers
// eslint-disable-next-line @typescript-eslint/no-unused-vars
const onDragEnter = (event: DragEvent) => {
  isDragOver.value = true
}

const onDragOver = (event: DragEvent) => {
  // This is called continuously while dragging over the element
  event.preventDefault()
}

// eslint-disable-next-line @typescript-eslint/no-unused-vars
const onDragLeave = (event: DragEvent) => {
  isDragOver.value = false
}

const onDrop = async (event: DragEvent) => {
  event.preventDefault()
  isDragOver.value = false

  const data = event.dataTransfer?.getData('application/json')
  if (!data) {
    return
  }

  try {
    const parsedData = JSON.parse(data)
    const { type } = parsedData

    const rect = canvasContainer.value?.getBoundingClientRect()
    if (!rect) {
      return
    }

    const x = (event.clientX - rect.left - position.value.x) / scale.value
    const y = (event.clientY - rect.top - position.value.y) / scale.value


    if (type === 'nautobot-device') {
      const { device } = parsedData as { type: string; device: NautobotDevice }

      // Check for duplicate by name first
      let existingDevice = deviceStore.findDeviceByName(device.name)

      // If not found by name, check by nautobot_id
      if (!existingDevice) {
        existingDevice = deviceStore.findDeviceByNautobotId(device.id)
      }

      if (existingDevice) {
        // Show duplicate dialog
        duplicateDeviceName.value = device.name
        duplicateExistingDevice.value = existingDevice
        pendingDeviceData.value = {
          name: device.name,
          device_type: mapNautobotDeviceType(device),
          ip_address: device.primary_ip4?.address?.split('/')[0],
          position_x: x - DEVICE_HALF_SIZE,
          position_y: y - DEVICE_HALF_SIZE,
          properties: JSON.stringify({
            nautobot_id: device.id,
            location: device.location?.name,
            role: device.role?.name,
            status: device.status?.name,
            device_model: device.device_type?.model,
            platform: device.platform?.network_driver,
            platform_id: device.platform?.id,
            device_type_model: device.device_type?.model,
            last_backup: device.cf_last_backup,
          }),
        }
        showDuplicateDialog.value = true
        return
      }

      // Debug: Log the Nautobot device object to see platform structure
      console.log('🔍 Creating device from Nautobot:', {
        name: device.name,
        platform: device.platform,
        platform_id: device.platform?.id,
        device_type: device.device_type,
        device_type_model: device.device_type?.model
      })

      deviceStore.createDevice({
        name: device.name,
        device_type: mapNautobotDeviceType(device),
        ip_address: device.primary_ip4?.address?.split('/')[0], // Remove CIDR notation
        position_x: x - DEVICE_HALF_SIZE, // Center the device
        position_y: y - DEVICE_HALF_SIZE,
        properties: JSON.stringify({
          nautobot_id: device.id,
          location: device.location?.name,
          role: device.role?.name,
          status: device.status?.name,
          device_model: device.device_type?.model,
          platform: device.platform?.network_driver,
          platform_id: device.platform?.id,
          device_type_model: device.device_type?.model,
          last_backup: device.cf_last_backup,
        }),
      })
    } else if (type === 'symbol') {
      const { symbol } = parsedData as { type: string; symbol: any }

      if (symbol.type === 'shape') {
        // Create a shape on the canvas
        const defaultWidth = symbol.shapeType === 'circle' ? 100 : 150
        const defaultHeight = symbol.shapeType === 'circle' ? 100 : 100

        shapesStore.createShape({
          shape_type: symbol.shapeType,
          position_x: x,
          position_y: y,
          width: defaultWidth,
          height: defaultHeight,
          fill_color: '#93c5fd',
          stroke_color: '#3b82f6',
          stroke_width: 2,
        })
      }
    }
  } catch (error) {
    console.error('❌ Failed to create device:', error)
  }
}

const onWheel = (event: any) => {
  event.evt.preventDefault()

  const scaleBy = SCALE_FACTOR
  const stage = event.target.getStage()
  const pointer = stage.getPointerPosition()
  const mousePointTo = {
    x: (pointer.x - stage.x()) / stage.scaleX(),
    y: (pointer.y - stage.y()) / stage.scaleY(),
  }

  const newScale = event.evt.deltaY > 0 ? scale.value / scaleBy : scale.value * scaleBy

  // Limit zoom
  if (newScale < 0.1 || newScale > 3) return

  canvasStore.setZoom(newScale)

  canvasStore.setPosition({
    x: pointer.x - mousePointTo.x * newScale,
    y: pointer.y - mousePointTo.y * newScale,
  })
}

const onStageMouseDown = (event: any) => {

  // Don't handle right-clicks here - they are handled by onRightClick and onDeviceMouseDown
  if (event.evt.button === 2) {
    return
  }

  // Check if clicking on a device - don't handle canvas operations if so
  if (event.target !== event.target.getStage()) {
    // Clicking on a device or device element, let device handlers take care of it
    return
  }

  if (event.target === event.target.getStage()) {
    console.log('🖱️ DEBUG: onStageMouseDown - clicking on stage, button:', event.evt.button, 'connectionRightClickInProgress:', connectionRightClickInProgress.value)

    // Don't deselect if right-clicking on a connection
    if (event.evt.button === 2 && connectionRightClickInProgress.value) {
      console.log('🖱️ DEBUG: onStageMouseDown - EARLY RETURN (connection right-click in progress)')
      return
    }

    mouseState.isDown = true
    const pos = event.target.getStage().getPointerPosition()
    mouseState.startX = pos.x
    mouseState.startY = pos.y

    console.log('🖱️ DEBUG: onStageMouseDown - about to deselect. selectedConnection before:', selectedConnection.value)
    selectedDevice.value = null
    selectedConnection.value = null  // Deselect connection when clicking canvas
    clearShapeSelection()  // Deselect shapes when clicking canvas
    console.log('🖱️ DEBUG: onStageMouseDown - selectedConnection after:', selectedConnection.value)
    hideContextMenu()

    // Only create selection box if Shift key is held down
    // Otherwise, default to canvas panning
    if (event.evt.shiftKey) {
      selectionBox.value = {
        startX: (pos.x - position.value.x) / scale.value,
        startY: (pos.y - position.value.y) / scale.value,
        endX: (pos.x - position.value.x) / scale.value,
        endY: (pos.y - position.value.y) / scale.value,
      }
    } else {
      selectionBox.value = null
      // Clear multi-selection when not holding shift
      selectedDevices.value.clear()
    }

  }
}

const onStageMouseMove = (event: any) => {
  if (!mouseState.isDown) return

  const pos = event.target.getStage().getPointerPosition()

  if (!mouseState.isDragging) {
    const dx = pos.x - mouseState.startX
    const dy = pos.y - mouseState.startY
    if (Math.abs(dx) > 3 || Math.abs(dy) > 3) {
      mouseState.isDragging = true
    }
  }

  if (mouseState.isDragging) {
    if (selectionBox.value) {
      // Update selection box (when Shift is held)
      selectionBox.value.endX = (pos.x - position.value.x) / scale.value
      selectionBox.value.endY = (pos.y - position.value.y) / scale.value
    } else {
      // Pan the canvas (default behavior)
      const deltaX = pos.x - mouseState.startX
      const deltaY = pos.y - mouseState.startY

      canvasStore.setPosition({
        x: position.value.x + deltaX,
        y: position.value.y + deltaY,
      })

      mouseState.startX = pos.x
      mouseState.startY = pos.y

      // Optional: Add some visual feedback
      // console.log('🔄 Panning canvas:', { deltaX, deltaY, newPos: { x: position.x, y: position.y } })
    }
  }
}

const onStageMouseUp = () => {

  // If we had a selection box, select devices within it
  if (selectionBox.value) {
    selectDevicesInBox(selectionBox.value)
  }

  mouseState.isDown = false
  mouseState.isDragging = false
  selectionBox.value = null
}

// Canvas mouse up now handled by useCanvasEvents composable
const onCanvasMouseUp = (event: MouseEvent) => {
  onGlobalMouseUp()
}

// Canvas right-click now handled by useCanvasEvents composable
const onRightClick = (event: MouseEvent) => {
  console.log('🖱️ DEBUG: onRightClick called, deviceRightClickInProgress:', deviceRightClickInProgress.value, 'connectionRightClickInProgress:', connectionRightClickInProgress.value)

  // Check if a device right-click is in progress
  if (deviceRightClickInProgress.value) {
    console.log('🖱️ DEBUG: onRightClick - device right-click in progress, returning')
    deviceRightClickInProgress.value = false // Reset flag
    return
  }

  // Check if a connection right-click is in progress
  if (connectionRightClickInProgress.value) {
    console.log('🖱️ DEBUG: onRightClick - connection right-click in progress, returning')
    connectionRightClickInProgress.value = false // Reset flag
    return
  }

  // Check if a device context menu was recently shown (within last 100ms)
  // This prevents canvas menu from overriding device menu
  if (contextMenu.show &&
      (contextMenu.targetType === 'device' || contextMenu.targetType === 'multi-device') &&
      Date.now() - contextMenuShownAt.value < 100) {
    return
  }

  // Check if a connection context menu was recently shown (within last 100ms)
  // This prevents canvas menu from overriding connection menu
  if (contextMenu.show &&
      contextMenu.targetType === 'connection' &&
      Date.now() - contextMenuShownAt.value < 100) {
    return
  }

  // Call composable handler for event prevention
  composableOnRightClick(null, { evt: event } as any)

  // Get the canvas container's bounding rect to calculate relative position
  const rect = canvasContainer.value?.getBoundingClientRect()
  if (!rect) {
    return
  }

  // Calculate position relative to the canvas container
  let menuX = event.clientX - rect.left
  let menuY = event.clientY - rect.top

  // Menu dimensions (approximate)
  const menuWidth = 200
  const menuHeight = 200

  // Ensure menu doesn't go outside the canvas bounds
  if (menuX + menuWidth > rect.width) {
    menuX = rect.width - menuWidth
  }
  if (menuY + menuHeight > rect.height) {
    menuY = rect.height - menuHeight
  }

  // Ensure menu doesn't go negative
  menuX = Math.max(0, menuX)
  menuY = Math.max(0, menuY)

  // Show canvas context menu
  showContextMenu(menuX, menuY, null, 'canvas')
}

// Device click now handled by useCanvasEvents composable
const onDeviceClick = (device: Device, event: any) => {
  // Call composable handler first
  composableOnDeviceClick(device, event)

  // Don't handle right-clicks in the click handler - they should be handled by mousedown only
  if (event.evt?.button === 2) {
    return
  }

  // Deselect any selected connection when clicking a device (unless shift is held)
  if (!event.evt?.shiftKey && selectedConnection.value !== null) {
    selectedConnection.value = null
  }

  // Handle device selection using the composable
  const isShiftClick = event.evt?.shiftKey || false
  composableSelectDevice(device, isShiftClick)

  // Don't hide context menu if it's showing a device context menu for this device
  // or if it's a multi-device menu and this device is part of the selection
  if (
    contextMenu.show &&
    ((contextMenu.targetType === 'device' && contextMenu.target?.id === device.id) ||
     (contextMenu.targetType === 'multi-device' && selectedDevices.value.has(device.id)))
  ) {
    return
  }

  // Hide context menu for other cases (canvas menu, or clicking different device)
  hideContextMenu()
}

// Device double-click now handled by useCanvasEvents composable
const onDeviceDoubleClick = (device: Device, event?: any) => {
  if (event) {
    composableOnDeviceDoubleClick(device, event)
  }
  editDevice(device)
}

const onDeviceMouseDown = (device: Device, event: any) => {
  // First call the composable handler for core logic
  composableOnDeviceMouseDown(device, event)
  

  // Check if it's a right-click (button 2)
  if (event.evt.button === 2) {
    
    // Set flag to prevent canvas right-click from overriding
    deviceRightClickInProgress.value = true
    

    // Prevent all event propagation
    event.evt.preventDefault()
    event.evt.stopPropagation()
    event.cancelBubble = true

    // Also stop immediate propagation to prevent other handlers
    if (event.evt.stopImmediatePropagation) {
      event.evt.stopImmediatePropagation()
    }

    // Check if the device is already part of a multi-selection
    const isDeviceInSelection = selectedDevices.value.has(device.id)
    const hasMultiSelection = selectedDevices.value.size > 1

    // If device is not in selection, or if it's a single selection, update selection
    if (!isDeviceInSelection || !hasMultiSelection) {
      // Clear current selection and select only this device
      selectedDevices.value.clear()
      selectedDevices.value.add(device.id)
      selectedDevice.value = device
      deviceStore.setSelectedDevice(device)
    } else {
    }

    // Get the canvas container's bounding rect to calculate relative position
    const rect = canvasContainer.value?.getBoundingClientRect()
    if (!rect) {
      return
    }

    // Calculate position relative to the canvas container
    let menuX = event.evt.clientX - rect.left
    let menuY = event.evt.clientY - rect.top

    // Menu dimensions (approximate)
    const menuWidth = 200
    const menuHeight = 200

    // Ensure menu doesn't go outside the canvas bounds
    if (menuX + menuWidth > rect.width) {
      menuX = rect.width - menuWidth
    }
    if (menuY + menuHeight > rect.height) {
      menuY = rect.height - menuHeight
    }

    // Ensure menu doesn't go negative
    menuX = Math.max(0, menuX)
    menuY = Math.max(0, menuY)


    // Show context menu using composable function
    const targetType = selectedDevices.value.size > 1 ? 'multi-device' : 'device'
    showContextMenu(menuX, menuY, device, targetType)

  } else {
  }
}

// Track which device is currently being dragged and its initial position
const dragState = ref<{
  draggedDevice: Device | null
  initialPositions: Map<number, { x: number; y: number }>
} | null>(null)

// Track real-time positions of devices during drag for connection rendering
const dragPositions = ref<Map<number, { x: number; y: number }>>(new Map())

const onDeviceDragStart = (device: Device) => {
  // Initialize drag state
  dragState.value = {
    draggedDevice: device,
    initialPositions: new Map()
  }
  
  // Store initial positions of all selected devices
  const selectedDevicesList = Array.from(selectedDevices.value)
    .map(id => deviceStore.devices.find(d => d.id === id))
    .filter((d): d is Device => d !== undefined)
  
  selectedDevicesList.forEach(selectedDevice => {
    dragState.value!.initialPositions.set(selectedDevice.id, {
      x: selectedDevice.position_x,
      y: selectedDevice.position_y
    })
  })
}

const onDeviceDragMove = (device: Device, event: any) => {
  const currentX = event.target.x()
  const currentY = event.target.y()

  // Update drag position for the dragged device for real-time connection rendering
  dragPositions.value.set(device.id, { x: currentX, y: currentY })

  // Handle multi-device dragging
  if (selectedDevices.value.size > 1 && selectedDevices.value.has(device.id) && dragState.value) {
    // Calculate the delta from the device's initial position
    const initialPos = dragState.value.initialPositions.get(device.id)
    if (!initialPos) return

    const deltaX = currentX - initialPos.x
    const deltaY = currentY - initialPos.y

    // Update positions of other selected devices in real-time in the store
    const otherSelectedDevices = Array.from(selectedDevices.value)
      .map(id => deviceStore.devices.find(d => d.id === id))
      .filter((d): d is Device => d !== undefined && d.id !== device.id)

    otherSelectedDevices.forEach(selectedDevice => {
      const initialDevicePos = dragState.value!.initialPositions.get(selectedDevice.id)
      if (!initialDevicePos) return

      const newX = initialDevicePos.x + deltaX
      const newY = initialDevicePos.y + deltaY

      // Update drag position for other selected devices for real-time connection rendering
      dragPositions.value.set(selectedDevice.id, { x: newX, y: newY })

      // Update the device position in the store in real-time
      // This will cause Vue's reactivity to update the visual position automatically
      deviceStore.updateDevice(selectedDevice.id, {
        position_x: newX,
        position_y: newY,
      })
    })
  }
}

const onDeviceDragEnd = (device: Device, event: any) => {
  const newX = event.target.x()
  const newY = event.target.y()

  try {
    // If multiple devices are selected, we only need to update the dragged device
    // since other devices were already updated during dragmove
    if (selectedDevices.value.size > 1 && selectedDevices.value.has(device.id)) {
      // Update the dragged device's final position
      deviceStore.updateDevice(device.id, {
        position_x: newX,
        position_y: newY,
      })
    } else {
      // Single device movement
      deviceStore.updateDevice(device.id, {
        position_x: newX,
        position_y: newY,
      })
    }
  } catch (error) {
    console.error('Failed to update device position:', error)
  }

  // Clean up drag state
  dragState.value = null

  // Clear all drag positions for connection rendering
  dragPositions.value.clear()
}

const onDeviceMouseEnter = () => {
  // Change cursor to pointer when hovering over devices
  if (canvasContainer.value) {
    canvasContainer.value.style.cursor = 'pointer'
  }
}

const onDeviceMouseLeave = () => {
  // Restore default canvas cursor when leaving device
  if (canvasContainer.value) {
    canvasContainer.value.style.cursor = mouseState.isDragging ? 'grabbing' : 'grab'
  }
}

const onConnectionMouseEnter = () => {
  // Change cursor to pointer when hovering over connections
  if (canvasContainer.value) {
    canvasContainer.value.style.cursor = 'pointer'
  }
}

const onConnectionMouseLeave = () => {
  // Restore default canvas cursor when leaving connection
  if (canvasContainer.value) {
    canvasContainer.value.style.cursor = mouseState.isDragging ? 'grabbing' : 'grab'
  }
}

// Shape handlers
// Wrapper for shape click that also clears device/connection selection
const handleShapeClick = (shape: any, event: any) => {
  selectedDevice.value = null
  selectedConnection.value = null
  onShapeClick(shape, event)
}

// Wrapper for shape right-click that passes showContextMenu
const onShapeRightClick = (shape: any, event: any) => {
  composableOnShapeRightClick(shape, event, showContextMenu)
}

// Connection click and context menu handlers
const onConnectionClick = (connection: any, event: any) => {
  event.cancelBubble = true

  // Don't handle click if it's a right-click (context menu)
  if (event.evt?.button === 2) {
    console.log('🔗 DEBUG: onConnectionClick - ignoring right-click')
    return
  }

  // Toggle selection: if already selected, deselect it
  if (selectedConnection.value === connection.id) {
    selectedConnection.value = null
    console.log('🔗 Connection deselected')
  } else {
    selectedConnection.value = connection.id
    console.log('🔗 Connection selected:', connection.id)
  }
}

const onConnectionRightClick = (connection: any, event: any) => {
  console.log('🔗 DEBUG: onConnectionRightClick called for connection:', connection.id)
  event.evt.preventDefault()
  event.evt.stopPropagation()
  event.cancelBubble = true

  // Set flag to prevent canvas right-click from overriding
  connectionRightClickInProgress.value = true
  console.log('🔗 DEBUG: connectionRightClickInProgress set to TRUE')

  // Select the connection
  selectedConnection.value = connection.id
  console.log('🔗 DEBUG: selectedConnection set to:', connection.id)

  // Get the canvas container's bounding rect to calculate relative position
  const rect = canvasContainer.value?.getBoundingClientRect()
  if (!rect) return

  // Calculate position relative to the canvas container
  let menuX = event.evt.clientX - rect.left
  let menuY = event.evt.clientY - rect.top

  // Menu dimensions (approximate)
  const menuWidth = 200
  const menuHeight = 200

  // Ensure menu doesn't go outside the canvas bounds
  if (menuX + menuWidth > rect.width) {
    menuX = rect.width - menuWidth
  }
  if (menuY + menuHeight > rect.height) {
    menuY = rect.height - menuHeight
  }

  // Ensure menu doesn't go negative
  menuX = Math.max(0, menuX)
  menuY = Math.max(0, menuY)

  console.log('🔗 DEBUG: About to show context menu')
  // Show context menu with connection as target
  showContextMenu(menuX, menuY, connection.id as any, 'connection' as any)
}

// Connection menu action functions
const showConnectionInfo = (connectionId: number) => {
  const connection = deviceStore.connections.find(c => c.id === connectionId)
  if (!connection) return

  const sourceDevice = deviceStore.devices.find(d => d.id === connection.source_device_id)
  const targetDevice = deviceStore.devices.find(d => d.id === connection.target_device_id)

  const info = `Connection ID: ${connection.id}
Source: ${sourceDevice?.name || 'Unknown'} (${sourceDevice?.ip_address || 'N/A'})
Target: ${targetDevice?.name || 'Unknown'} (${targetDevice?.ip_address || 'N/A'})
Type: ${connection.connection_type}
Properties: ${JSON.stringify(connection.properties || {}, null, 2)}`

  alert(info)
}

const showConnectionStatus = (connectionId: number) => {
  const connection = deviceStore.connections.find(c => c.id === connectionId)
  if (!connection) return

  console.log('📊 Show connection status:', connectionId)
  // TODO: Implement connection status display
  alert('Connection Status feature coming soon!')
}

const showConnectionStats = (connectionId: number) => {
  const connection = deviceStore.connections.find(c => c.id === connectionId)
  if (!connection) return

  console.log('📈 Show connection stats:', connectionId)
  // TODO: Implement connection stats display
  alert('Connection Stats feature coming soon!')
}

const deleteConnection = (connectionId: number) => {
  const connection = deviceStore.connections.find(c => c.id === connectionId)
  if (!connection) return

  const sourceDevice = deviceStore.devices.find(d => d.id === connection.source_device_id)
  const targetDevice = deviceStore.devices.find(d => d.id === connection.target_device_id)

  if (confirm(`Delete connection between ${sourceDevice?.name} and ${targetDevice?.name}?`)) {
    // Remove connection from the store's connections array
    const index = deviceStore.connections.findIndex(c => c.id === connectionId)
    if (index !== -1) {
      deviceStore.connections.splice(index, 1)
      selectedConnection.value = null
      console.log('✅ Connection deleted:', connectionId)
    }
  }
}

const onConnectionPointClick = (device: Device, point: { x: number; y: number }, event: any) => {
  event.cancelBubble = true

  if (!connectionMode.value) return

  if (!connectionStart.value) {
    connectionStart.value = { device, point }
  } else {
    if (connectionStart.value.device.id !== device.id) {
      try {
        deviceStore.createConnection({
          source_device_id: connectionStart.value.device.id,
          target_device_id: device.id,
          connection_type: 'ethernet',
        })
      } catch (error) {
        console.error('Failed to create connection:', error)
      }
    }
    connectionStart.value = null
    connectionMode.value = false
  }
}

// Canvas controls - now handled by useCanvasControls composable

// Device search functions
const toggleDeviceSearch = () => {
  showDeviceSearch.value = !showDeviceSearch.value
  if (showDeviceSearch.value) {
    deviceSearchQuery.value = ''
    // Focus the input after DOM updates
    nextTick(() => {
      deviceSearchInput.value?.focus()
    })
  }
}

const closeDeviceSearch = () => {
  showDeviceSearch.value = false
  deviceSearchQuery.value = ''
}

const searchAndCenterDevice = () => {
  const query = deviceSearchQuery.value.trim().toLowerCase()
  if (!query) return

  // Find device by name (case-insensitive)
  const foundDevice = deviceStore.devices.find((device) =>
    device.name.toLowerCase().includes(query)
  )

  if (foundDevice) {
    // Center the device on screen
    const containerRect = canvasContainer.value?.getBoundingClientRect()
    if (containerRect) {
      canvasStore.setPosition({
        x: containerRect.width / 2 - (foundDevice.position_x + DEVICE_HALF_SIZE) * scale.value,
        y: containerRect.height / 2 - (foundDevice.position_y + DEVICE_HALF_SIZE) * scale.value,
      })

      // Select the device
      deviceStore.setSelectedDevice(foundDevice)

      // Close search
      closeDeviceSearch()

    }
  } else {
    // Optionally show a notification that device was not found
  }
}

// Context menu actions - now handled by composables  
const deleteDevice = composableDeleteDevice
const editDevice = composableEditDevice

// eslint-disable-next-line @typescript-eslint/no-unused-vars

const centerOnDevice = (device: Device) => {
  const containerRect = canvasContainer.value?.getBoundingClientRect()
  if (!containerRect) return

  canvasStore.setPosition({
    x: containerRect.width / 2 - (device.position_x + DEVICE_HALF_SIZE) * scale.value,
    y: containerRect.height / 2 - (device.position_y + DEVICE_HALF_SIZE) * scale.value,
  })
  hideContextMenu()
}

// Device operations now handled by useDeviceOperations composable

// Resize handler
const handleResize = () => {
  if (canvasContainer.value) {
    const newWidth = canvasContainer.value.clientWidth
    const newHeight = canvasContainer.value.clientHeight

    // Only update if dimensions are valid, with minimum fallback
    if (newWidth > 0 && newHeight > 0) {
      canvasSize.width = newWidth
      canvasSize.height = newHeight
    } else if (canvasContainer.value.parentElement) {
      // Fallback to parent element dimensions
      const parentWidth = canvasContainer.value.parentElement.clientWidth
      const parentHeight = canvasContainer.value.parentElement.clientHeight
      if (parentWidth > 0 && parentHeight > 0) {
        canvasSize.width = parentWidth
        canvasSize.height = parentHeight
      }
    }
  }
}

// Global click handler to hide context menu
const handleGlobalClick = (event: MouseEvent) => {

  // Don't handle right-clicks - they should show context menus, not hide them
  if (event.button === 2) {
    return
  }

  if (contextMenu.show) {
    // Prevent hiding context menu too soon after it was shown (race condition)
    const timeSinceShown = Date.now() - contextMenuShownAt.value

    if (timeSinceShown < 100) {
      return
    }

    // Find the context menu element using data attribute
    const contextMenuElement = document.querySelector('[data-context-menu="true"]')
    const clickedInsideMenu = contextMenuElement?.contains(event.target as Node)


    if (!clickedInsideMenu) {
      hideContextMenu()
    } else {
    }
  }
}

// Global mouseup handler to hide context menu on left-click release only
const handleGlobalMouseUp = (event: MouseEvent) => {


  // Only hide context menu on left-click mouseup, never on right-click
  if (event.button === 0 && contextMenu.show) {
    
    // Prevent hiding context menu too soon after it was shown (race condition)
    const timeSinceShown = Date.now() - contextMenuShownAt.value

    if (timeSinceShown < 100) {
      return
    }

    // Find the context menu element using data attribute
    const contextMenuElement = document.querySelector('[data-context-menu="true"]')
    const clickedInsideMenu = contextMenuElement?.contains(event.target as Node)


    if (!clickedInsideMenu) {
      hideContextMenu()
    } else {
    }
  } else if (event.button === 2) {
  }
}

// Global keyboard handler for shortcuts
const handleGlobalKeyDown = (event: KeyboardEvent) => {
  // Handle Ctrl+S (or Cmd+S on Mac) for save
  if ((event.ctrlKey || event.metaKey) && event.key === 's') {
    event.preventDefault() // Prevent browser's default save behavior
    saveCanvas()
  }
}

// Browser beforeunload event handler to warn about unsaved changes
const handleBeforeUnload = (event: BeforeUnloadEvent) => {
  if (composableHasUnsavedChanges.value) {
    event.preventDefault()
    // Modern browsers ignore custom messages and show their own
    event.returnValue = 'You have unsaved changes. Are you sure you want to leave?'
    return 'You have unsaved changes. Are you sure you want to leave?'
  }
}

// Handlers for unsaved changes dialog
const handleUnsavedChangesSave = () => {
  showUnsavedChangesDialog.value = false
  // Show save modal - after save completes, the pending action will need to be called manually
  composableShowSaveModal.value = true
  // Note: The pending action will be called after successful save in handleCanvasSave
}

const handleUnsavedChangesDiscard = () => {
  showUnsavedChangesDialog.value = false
  // Execute the pending action without saving
  if (pendingAction.value) {
    pendingAction.value()
    pendingAction.value = null
  }
}

onMounted(async () => {
  await nextTick()

  // Load device icons and templates first
  // Note: Shapes are NOT loaded here - they're only loaded when a canvas is loaded
  await Promise.all([
    loadDeviceIcons(),
    templateService.fetchTemplates()
  ])

  // Debug: Check device count

  // Ensure canvas container is available before initializing
  if (canvasContainer.value) {
    // Wait a bit more for the DOM to be fully rendered
    setTimeout(() => {
      handleResize()

      // If still no dimensions after first resize, try again
      if (canvasSize.width === 0 || canvasSize.height === 0) {
        setTimeout(() => {
          handleResize()
        }, 200)
      }
    }, 100)
  }

  window.addEventListener('resize', handleResize)
  window.addEventListener('beforeunload', handleBeforeUnload)
  document.addEventListener('click', handleGlobalClick)
  document.addEventListener('mouseup', handleGlobalMouseUp)
  document.addEventListener('keydown', handleGlobalKeyDown)
})

onUnmounted(() => {
  window.removeEventListener('resize', handleResize)
  window.removeEventListener('beforeunload', handleBeforeUnload)
  document.removeEventListener('click', handleGlobalClick)
  document.removeEventListener('mouseup', handleGlobalMouseUp)
  document.removeEventListener('keydown', handleGlobalKeyDown)
})
</script>

<style scoped>
.canvas-container {
  cursor: grab;
}

.canvas-container:active {
  cursor: grabbing;
}

/* Context Menu Submenu Hover Effects */
.context-menu-item {
  position: relative;
}

.context-menu-item > .submenu {
  opacity: 0;
  visibility: hidden;
  transform: translateX(-10px);
  transition:
    opacity 0.2s ease-out,
    visibility 0.2s ease-out,
    transform 0.2s ease-out;
}

.context-menu-item:hover > .submenu {
  opacity: 1;
  visibility: visible;
  transform: translateX(0);
}

/* Keep submenu visible when hovering over it */
.context-menu-item:hover > .submenu,
.submenu:hover {
  opacity: 1;
  visibility: visible;
}

/* Extend hover area slightly to prevent flickering */
.context-menu-item:hover::after {
  content: '';
  position: absolute;
  top: 0;
  right: -5px;
  width: 5px;
  height: 100%;
  z-index: 1;
}
</style>
