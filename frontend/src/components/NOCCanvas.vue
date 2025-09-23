<template>
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
            stroke: '#3b82f6',
            strokeWidth: 2,
            opacity: 0.8,
          }"
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
            v-if="getDeviceIcon(device.device_type)"
            :config="{
              x: 16,
              y: 16,
              width: 28,
              height: 28,
              image: getDeviceIcon(device.device_type),
            }"
          />

          <!-- Device Name -->
          <v-text
            :config="{
              x: DEVICE_HALF_SIZE,
              y: DEVICE_TEXT_Y_OFFSET,
              text: device.name,
              fontSize: 9,
              align: 'center',
              fill: '#374151',
              fontFamily: 'Arial',
              offsetX: device.name.length * 5.5,
              offsetY: DEVICE_NAME_OFFSET_Y,
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

              <!-- Nested Submenu -->
              <div
                v-if="subItem.submenu"
                class="submenu absolute left-full top-0 bg-white/95 backdrop-blur-md border border-gray-200/60 rounded-lg shadow-2xl shadow-black/10 py-1 min-w-36 z-10"
                data-context-menu="true"
              >
                <button
                  v-for="nestedItem in subItem.submenu"
                  :key="nestedItem.label"
                  @click="nestedItem.action()"
                  class="w-full text-left px-3 py-1.5 text-xs text-gray-700 hover:bg-gradient-to-r hover:from-blue-50/80 hover:to-indigo-50/80 hover:text-blue-900 flex items-center space-x-2 transition-all duration-150 ease-out"
                >
                  <span class="text-xs opacity-70">{{ nestedItem.icon }}</span>
                  <span class="font-medium">{{ nestedItem.label }}</span>
                </button>
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
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, computed, onMounted, onUnmounted, nextTick } from 'vue'
import { useDevicesStore, type Device } from '@/stores/devices'
import { useCanvasStore } from '@/stores/canvas'
import { type NautobotDevice, canvasApi } from '@/services/api'
import { useDeviceIcons } from '@/composables/useDeviceIcons'
import { useCanvasControls } from '@/composables/useCanvasControls'
import { useDeviceSelection } from '@/composables/useDeviceSelection'
import { useContextMenu } from '@/composables/useContextMenu'
import { useCanvasState } from '@/composables/useCanvasState'
import { useDeviceOperations } from '@/composables/useDeviceOperations'
import { useCanvasEvents } from '@/composables/useCanvasEvents'
import { useCommands } from '@/composables/useCommands'
import SaveCanvasModal from './SaveCanvasModal.vue'
import ConfirmDialog from './ConfirmDialog.vue'
import LoadCanvasModal from './LoadCanvasModal.vue'
import DuplicateDeviceModal from './DuplicateDeviceModal.vue'

// Constants
const DEVICE_SIZE = 60
const DEVICE_HALF_SIZE = 30
const GRID_SIZE = 50
const SCALE_FACTOR = 1.1
const DEVICE_NAME_OFFSET_Y = 10
const DEVICE_TEXT_Y_OFFSET = 50

const deviceStore = useDevicesStore()
const canvasStore = useCanvasStore()
const { loadDeviceIcons, getDeviceIcon } = useDeviceIcons()

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

// Connection state
const connectionStart = ref<{
  device: Device
  point: { x: number; y: number }
} | null>(null)

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

// Execute a command on a device
const executeCommand = (device: Device, command: any) => {
  console.log(`🚀 Executing command on ${device.name} (${command.platform}):`)
  console.log(`Command: ${command.command}`)
  console.log(`Parser: ${command.parser}`)
  
  // Mock implementation - show a simple alert for now
  alert(`Executing command on ${device.name}:\n\n"${command.command}"\n\nPlatform: ${command.platform}\nParser: ${command.parser}\n\n(This is a mock - actual execution will be implemented later)`)
  
  hideContextMenu()
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

      return {
        id: connection.id,
        points: [
          sourceDevice.position_x + DEVICE_HALF_SIZE,
          sourceDevice.position_y + DEVICE_HALF_SIZE,
          targetDevice.position_x + DEVICE_HALF_SIZE,
          targetDevice.position_y + DEVICE_HALF_SIZE,
        ],
      }
    })
    .filter((connection): connection is NonNullable<typeof connection> => connection !== null)
})

// Context menu items
const contextMenuItems = computed(() => {
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
      { icon: '🔗', label: 'Show All Neighbors', action: () => { hideContextMenu(); showMultiDeviceNeighbors() } },
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
        { icon: '👁️', label: 'Show', action: () => { hideContextMenu(); showDeviceConfig(contextMenu.target!) } },
        { icon: '📝', label: 'Show Changes', action: () => { hideContextMenu(); showDeviceChanges(contextMenu.target!) } },
      ],
    },
    {
      icon: '💻',
      label: 'Commands',
      submenu: commandsSubmenu
    },
    { icon: '🔗', label: 'Neighbors', action: () => { hideContextMenu(); showDeviceNeighbors(contextMenu.target!) } },
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

    // Clear current canvas first if it has devices
    if (deviceStore.devices.length > 0) {
      deviceStore.clearDevices()
    }

    // Fetch canvas data
    const canvas = await canvasApi.getCanvas(canvasId)

    // Load devices and connections directly from canvas data (pure frontend)
    // Convert CanvasDeviceData to Device with proper types
    const devicesWithCorrectTypes = canvas.canvas_data.devices.map((device) => ({
      ...device,
      device_type: device.device_type as Device['device_type'],
    }))

    deviceStore.loadDevicesFromCanvasData(devicesWithCorrectTypes, canvas.canvas_data.connections)

    // Update tracking state
    composableCanvasId.value = canvasId
    updateSavedState()

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
    // Import the canvas API
    const { canvasApi } = await import('@/services/api')

    // Collect current canvas state
    const canvasData = {
      devices: deviceStore.devices.map((device) => ({
        id: device.id,
        name: device.name,
        device_type: device.device_type,
        ip_address: device.ip_address,
        position_x: device.position_x,
        position_y: device.position_y,
        properties: device.properties,
      })),
      connections: deviceStore.connections.map((connection) => ({
        id: connection.id,
        source_device_id: connection.source_device_id,
        target_device_id: connection.target_device_id,
        connection_type: connection.connection_type,
        properties: connection.properties,
      })),
    }

    let response
    if (data.canvasId) {
      // Update existing canvas
      response = await canvasApi.updateCanvas(data.canvasId, {
        name: data.name,
        sharable: data.sharable,
        canvas_data: canvasData,
      })
      composableCanvasId.value = data.canvasId
    } else {
      // Create new canvas
      response = await canvasApi.saveCanvas({
        name: data.name,
        sharable: data.sharable,
        canvas_data: canvasData,
      })
      composableCanvasId.value = response.id
    }

    // Update saved state after successful save
    updateSavedState()

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

const showDeviceConfig = (device: Device) => {
}

const showDeviceChanges = (device: Device) => {
}

const showDeviceCommands = (device: Device) => {
}

const showDeviceNeighbors = (device: Device) => {
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
            last_backup: device.cf_last_backup,
          }),
        }
        showDuplicateDialog.value = true
        return
      }

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
          last_backup: device.cf_last_backup,
        }),
      })
    } else {
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
    mouseState.isDown = true
    const pos = event.target.getStage().getPointerPosition()
    mouseState.startX = pos.x
    mouseState.startY = pos.y

    selectedDevice.value = null
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
  
  // Check if a device right-click is in progress
  if (deviceRightClickInProgress.value) {
    deviceRightClickInProgress.value = false // Reset flag
    return
  }
  
  // Check if a device context menu was recently shown (within last 100ms)
  // This prevents canvas menu from overriding device menu
  if (contextMenu.show && 
      (contextMenu.targetType === 'device' || contextMenu.targetType === 'multi-device') &&
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
  // Only handle multi-device dragging during dragmove
  if (selectedDevices.value.size > 1 && selectedDevices.value.has(device.id) && dragState.value) {
    const currentX = event.target.x()
    const currentY = event.target.y()

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

      // Update the device position in the store in real-time
      // This will cause Vue's reactivity to update the visual position automatically
      deviceStore.updateDevice(selectedDevice.id, {
        position_x: initialDevicePos.x + deltaX,
        position_y: initialDevicePos.y + deltaY,
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

  // Load device icons first
  await loadDeviceIcons()

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

.context-menu-item .submenu {
  opacity: 0;
  visibility: hidden;
  transform: translateX(-10px);
  transition:
    opacity 0.2s ease-out,
    visibility 0.2s ease-out,
    transform 0.2s ease-out;
}

.context-menu-item:hover .submenu {
  opacity: 1;
  visibility: visible;
  transform: translateX(0);
}

/* Keep submenu visible when hovering over it */
.context-menu-item:hover .submenu,
.submenu:hover {
  opacity: 1;
  visibility: visible;
}

/* Handle nested submenus */
.context-menu-item .context-menu-item:hover .submenu {
  opacity: 1;
  visibility: visible;
  transform: translateX(0);
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
