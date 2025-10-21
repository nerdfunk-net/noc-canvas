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

      <!-- Background Shapes Layer (renders behind devices) -->
      <v-layer ref="backgroundLayer" :config="{ visible: layerVisibility.background }">
        <v-group
          v-for="shape in backgroundShapes"
          :key="`shape-bg-${shape.id}`"
          :config="{
            x: shape.position_x,
            y: shape.position_y,
            draggable: true,
          }"
          @dragstart="onShapeDragStart(shape)"
          @dragmove="onShapeDragMove(shape, $event)"
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
      </v-layer>

      <!-- Layer2 Connections (CDP, MAC) - renders below devices -->
      <v-layer ref="layer2ConnectionsLayer" :config="{ visible: layerVisibility.layer2 }">
        <v-line
          v-for="connection in layer2Connections"
          :key="`connection-${connection.id}`"
          :config="{
            points: connection.points,
            stroke: selectedConnection === connection.id ? '#10b981' : '#34d399',
            strokeWidth: selectedConnection === connection.id ? 4 : 2,
            opacity: selectedConnection === connection.id ? 1 : 0.8,
            hitStrokeWidth: 10,
          }"
          @click="onConnectionClick(connection, $event)"
          @contextmenu="onConnectionRightClick(connection, $event)"
          @mouseenter="onConnectionMouseEnter"
          @mouseleave="onConnectionMouseLeave"
        />

        <!-- Waypoints for selected Layer2 connection -->
        <template v-if="selectedConnection && isLayer2Connection(selectedConnection)">
          <v-circle
            v-for="(waypoint, index) in getConnectionWaypoints(selectedConnection)"
            :key="`waypoint-${selectedConnection}-${index}`"
            :config="{
              x: waypoint.x,
              y: waypoint.y,
              radius: 6,
              fill: '#10b981',
              stroke: '#ffffff',
              strokeWidth: 2,
              draggable: true,
            }"
            @dragstart="onWaypointDragStart(selectedConnection, index)"
            @dragmove="onWaypointDragMove(selectedConnection, index, $event)"
            @dragend="onWaypointDragEnd"
            @contextmenu="onWaypointRightClick(selectedConnection, index, $event)"
            @mouseenter="(e: any) => e.target.getStage().container().style.cursor = 'move'"
            @mouseleave="(e: any) => e.target.getStage().container().style.cursor = 'default'"
          />
        </template>
      </v-layer>

      <!-- Devices Layer (renders above background) -->
      <v-layer ref="devicesLayer" :config="{ visible: layerVisibility.devices }">
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
              radius: point.label ? 5 : 4,
              fill: point.label ? '#3b82f6' : '#10b981',
              stroke: point.label ? '#1e40af' : '#065f46',
              strokeWidth: point.label ? 2 : 1,
              opacity: connectionMode ? 1 : 0,
              draggable: point.label ? true : false,
            }"
            @click="onConnectionPointClick(device, point, $event)"
            @contextmenu="onConnectionPointRightClick(device, point, $event)"
            @dragstart="onConnectionPortDragStart(device, point, $event)"
            @dragmove="onConnectionPortDragMove(device, point, $event)"
            @dragend="onConnectionPortDragEnd(device, point, $event)"
            @mouseenter="(e: any) => { if (point.label) e.target.getStage().container().style.cursor = 'move' }"
            @mouseleave="(e: any) => e.target.getStage().container().style.cursor = 'default'"
          />
          
          <!-- Connection Point Labels (for custom ports) -->
          <v-text
            v-for="(point, index) in getConnectionPoints(device).filter(p => p.label)"
            :key="`point-label-${device.id}-${index}`"
            :config="{
              x: point.x + 8,
              y: point.y - 6,
              text: point.label,
              fontSize: 8,
              fill: '#1e40af',
              fontFamily: 'Arial',
              fontStyle: 'bold',
              opacity: connectionMode ? 1 : 0,
            }"
          />
        </v-group>
      </v-layer>

      <!-- Device Shapes Layer (renders above devices) -->
      <v-layer ref="shapesLayer">
        <v-group
          v-for="shape in deviceLayerShapes"
          :key="`shape-dev-${shape.id}`"
          :config="{
            x: shape.position_x,
            y: shape.position_y,
            draggable: true,
          }"
          @dragstart="onShapeDragStart(shape)"
          @dragmove="onShapeDragMove(shape, $event)"
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

      <!-- Layer3 Connections (IP ARP, Static, OSPF, BGP) - renders above devices -->
      <v-layer ref="layer3ConnectionsLayer" :config="{ visible: layerVisibility.layer3 }">
        <v-line
          v-for="connection in layer3Connections"
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

        <!-- Waypoints for selected Layer3 connection -->
        <template v-if="selectedConnection && isLayer3Connection(selectedConnection)">
          <v-circle
            v-for="(waypoint, index) in getConnectionWaypoints(selectedConnection)"
            :key="`waypoint-${selectedConnection}-${index}`"
            :config="{
              x: waypoint.x,
              y: waypoint.y,
              radius: 6,
              fill: '#1d4ed8',
              stroke: '#ffffff',
              strokeWidth: 2,
              draggable: true,
            }"
            @dragstart="onWaypointDragStart(selectedConnection, index)"
            @dragmove="onWaypointDragMove(selectedConnection, index, $event)"
            @dragend="onWaypointDragEnd"
            @contextmenu="onWaypointRightClick(selectedConnection, index, $event)"
            @mouseenter="(e: any) => e.target.getStage().container().style.cursor = 'move'"
            @mouseleave="(e: any) => e.target.getStage().container().style.cursor = 'default'"
          />
        </template>
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

    <!-- Connection Mode Help Text -->
    <div v-if="connectionMode" class="absolute top-4 left-1/2 transform -translate-x-1/2 z-10">
      <div class="bg-green-50 border border-green-200 rounded-lg shadow-lg px-4 py-2 text-sm">
        <div class="flex items-center space-x-2">
          <span class="text-green-600 font-semibold">🔗 Connection Mode Active</span>
          <span class="text-gray-600">|</span>
          <span class="text-gray-700">Alt+Click device to add port</span>
          <span class="text-gray-600">|</span>
          <span class="text-gray-700">Drag port to move</span>
          <span class="text-gray-600">|</span>
          <span class="text-gray-700">Right-click port to delete</span>
          <span class="text-gray-600">|</span>
          <span class="text-gray-700">Click ports to connect</span>
        </div>
      </div>
    </div>

    <!-- Canvas Controls -->
    <div class="absolute bottom-4 right-4 flex flex-col space-y-2">
      <button
        @click="toggleGrid"
        class="p-2 bg-white border border-gray-200 rounded-lg shadow-sm hover:bg-gray-50 flex-shrink-0"
        :class="{ 'bg-primary-50 border-primary-200': showGrid }"
        title="Toggle Grid"
      >
        📐
      </button>
      <button
        @click="toggleSnapToGrid"
        class="p-2 bg-white border border-gray-200 rounded-lg shadow-sm hover:bg-gray-50 flex-shrink-0 text-xl"
        :class="{ 'bg-purple-50 border-purple-200': snapToGrid }"
        :title="snapToGrid ? 'Snap to Grid: ON\nDevices snap to grid points' : 'Snap to Grid: OFF\nClick to enable grid snapping'"
      >
        {{ snapToGrid ? '🔒' : '🔓' }}
      </button>
      <button
        @click="toggleConnectionMode"
        class="p-2 bg-white border border-gray-200 rounded-lg shadow-sm hover:bg-gray-50 flex-shrink-0"
        :class="{ 'bg-green-50 border-green-200': connectionMode }"
        title="Connection Mode&#10;• Alt+Click device to add port&#10;• Drag port to reposition&#10;• Right-click port to delete&#10;• Click ports to connect"
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

    <!-- Topology Discovery Modal -->
    <TopologyDiscoveryModal
      :is-open="showTopologyDiscoveryModal"
      @close="showTopologyDiscoveryModal = false"
      @openBuilder="openTopologyBuilderFromDiscovery"
    />

    <!-- Topology Builder Modal -->
    <TopologyBuilderModal
      :is-open="showTopologyBuilderModal"
      @close="showTopologyBuilderModal = false"
      @import="handleTopologyImport"
    />

    <!-- Device Interfaces Modal -->
    <DeviceInterfacesModal
      :show="showInterfacesModal"
      :device-id="interfacesDeviceId"
      :device-name="interfacesDeviceName"
      @close="closeInterfacesModal"
    />

    <!-- SSH Terminal Modal -->
    <SSHTerminalModal
      :show="showSSHTerminalModal"
      :device-id="sshTerminalDeviceId"
      :device-name="sshTerminalDeviceName"
      @close="closeSSHTerminalModal"
    />

    <!-- Device Overview Modal -->
    <DeviceOverviewModal
      :show="showDeviceOverviewModal"
      :device-id="deviceOverviewId"
      @close="closeDeviceOverviewModal"
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

    <!-- Auto-save Restore Dialog -->
    <ConfirmDialog
      :show="showAutosaveRestoreDialog"
      title="Restore Auto-saved Canvas"
      message="An auto-saved canvas was found from your previous session. Would you like to restore it?"
      confirm-text="Restore"
      cancel-text="Start Fresh"
      @confirm="handleAutosaveRestore"
      @cancel="handleAutosaveDiscard"
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

    <!-- Baseline Exists Modal -->
    <BaselineExistsModal
      :show="showBaselineExistsModal"
      :device-name="baselineModalData.device?.name || ''"
      :baseline-data="baselineModalData.baselineData || {}"
      @close="showBaselineExistsModal = false"
      @overwrite="handleBaselineOverwrite"
    />

    <!-- Snapshot List Modal -->
    <SnapshotListModal
      :show="showSnapshotListModal"
      :device-id="currentSnapshotDeviceId"
      @close="showSnapshotListModal = false"
      @show="handleShowSnapshotDetails"
    />

    <!-- Snapshot Details Modal -->
    <SnapshotDetailsModal
      :show="showSnapshotDetailsModal"
      :snapshot-id="currentSnapshotId"
      @close="showSnapshotDetailsModal = false"
    />

    <!-- Compare Snapshot to Baseline Modal -->
    <CompareSnapshotModal
      :show="showCompareModal"
      :device-id="currentCompareDeviceId"
      @close="showCompareModal = false"
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
import { useAuthStore } from '@/stores/auth'
import { type NautobotDevice, canvasApi, nautobotApi, makeAuthenticatedRequest } from '@/services/api'
import secureStorage from '@/services/secureStorage'
import { useDeviceIcons } from '@/composables/useDeviceIcons'
import { templateService } from '@/services/templateService'
import { useCanvasControls } from '@/composables/useCanvasControls'
import { useDeviceSelection } from '@/composables/useDeviceSelection'
import { useContextMenu } from '@/composables/useContextMenu'
import { useContextMenuItems } from '@/composables/useContextMenuItems'
import { useModals } from '@/composables/useModals'
import { useConnectionRendering } from '@/composables/useConnectionRendering'
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
import TopologyBuilderModal from './TopologyBuilderModal.vue'
import TopologyDiscoveryModal from './TopologyDiscoveryModal.vue'
import DeviceInterfacesModal from './DeviceInterfacesModal.vue'
import SSHTerminalModal from './SSHTerminalModal.vue'
import DeviceOverviewModal from './DeviceOverviewModal.vue'
import BaselineExistsModal from './BaselineExistsModal.vue'
import SnapshotListModal from './SnapshotListModal.vue'
import SnapshotDetailsModal from './SnapshotDetailsModal.vue'
import CompareSnapshotModal from './CompareSnapshotModal.vue'
import type { TopologyGraph } from '@/services/api'
import { openTerminalWindow, canOpenPopup } from '@/utils/terminalWindow'

// Constants
const DEVICE_SIZE = 60
const DEVICE_HALF_SIZE = 30
const GRID_SIZE = 50
const SCALE_FACTOR = 1.1
const DEVICE_NAME_OFFSET_Y = 10
const DEVICE_TEXT_Y_OFFSET = 50

// Snap-to-grid feature
const snapToGrid = ref(false)

// Toggle snap to grid function
const toggleSnapToGrid = () => {
  snapToGrid.value = !snapToGrid.value
  console.log('🧲 Snap to Grid:', snapToGrid.value ? 'ENABLED ✅' : 'DISABLED ❌')
}

// Helper function to snap coordinates to grid
const snapToGridCoordinates = (x: number, y: number): { x: number; y: number } => {
  if (!snapToGrid.value) {
    return { x, y }
  }
  const snapped = {
    x: Math.round(x / GRID_SIZE) * GRID_SIZE,
    y: Math.round(y / GRID_SIZE) * GRID_SIZE
  }
  console.log(`📍 Snapping (${x.toFixed(0)}, ${y.toFixed(0)}) → (${snapped.x}, ${snapped.y})`)
  return snapped
}

const deviceStore = useDevicesStore()
const canvasStore = useCanvasStore()
const shapesStore = useShapesStore()
const authStore = useAuthStore()
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

    // If we have platform or device type info, try to get icon from template service
    if (platformId || deviceTypeModel) {
      const templateIcon = await templateService.getDeviceIcon(platformId, deviceTypeModel)
      if (templateIcon) {
        console.log('✅ Using template icon for device:', device.name, 'from platform:', platformId, 'or model:', deviceTypeModel)
        // Create new Map to trigger reactivity
        deviceIconMap.value = new Map(deviceIconMap.value).set(device.id, templateIcon)
        console.log('🔄 Icon map updated, map size:', deviceIconMap.value.size)
        return
      } else {
        console.log('⚠️ No template icon found for device:', device.name, 'platform:', platformId, 'model:', deviceTypeModel)
      }
    } else {
      console.log('⚠️ No platform_id or device_type_model in device properties for:', device.name)
    }

    // Use hardcoded icon as fallback
    console.log('🔄 Using fallback hardcoded icon for device:', device.name, 'type:', device.device_type)
    const fallbackIcon = getHardcodedIcon(device.device_type)
    if (fallbackIcon) {
      deviceIconMap.value = new Map(deviceIconMap.value).set(device.id, fallbackIcon)
    }
  } catch (error) {
    console.error('❌ Error loading device icon for', device.name, ':', error)
  }
}

// Watch for device changes and load template icons
watch(() => deviceStore.devices, async (devices) => {
  // If devices array is empty, clear the icon map
  if (devices.length === 0) {
    console.log('🧹 Clearing device icon map (devices cleared)')
    deviceIconMap.value = new Map()
    return
  }

  // Load icons for new devices
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

// Initialize device selection composable first
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

// Now initialize shape operations with selectedDevices
const shapeOperationsComposable = useShapeOperations(selectedDevices, deviceStore)
const {
  selectedShape,
  selectedShapes,
  transformer,
  showShapeColorModal,
  shapeColorToEdit,
  currentShapeColors,
  onShapeClick,
  onShapeDragStart,
  onShapeDragMove,
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

// Create a wrapper for selectDevicesInBox that also selects shapes
const selectDevicesInBox = (box: { startX: number; startY: number; endX: number; endY: number }) => {
  composableSelectDevicesInBox(box)

  // Also select shapes in the box
  const minX = Math.min(box.startX, box.endX)
  const maxX = Math.max(box.startX, box.endX)
  const minY = Math.min(box.startY, box.endY)
  const maxY = Math.max(box.startY, box.endY)

  const shapesStore = useShapesStore()
  const newShapeSelection = new Set(selectedShapes.value)

  shapesStore.shapes.forEach((shape) => {
    const shapeLeft = shape.position_x
    const shapeRight = shape.position_x + shape.width
    const shapeTop = shape.position_y
    const shapeBottom = shape.position_y + shape.height

    const overlapsX = shapeLeft < maxX && shapeRight > minX
    const overlapsY = shapeTop < maxY && shapeBottom > minY

    if (overlapsX && overlapsY) {
      newShapeSelection.add(shape.id)
      console.log('✅ Selected shape:', shape.shape_type, 'at', shape.position_x, shape.position_y)
    }
  })

  selectedShapes.value = newShapeSelection
  console.log(`🎯 Total shapes selected: ${selectedShapes.value.size}`)
}

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

// Auto-save functionality
const autoSaveTimer = ref<number | null>(null)
const autoSaveSettings = ref<{ enabled: boolean; interval: number }>({ enabled: false, interval: 60 })

// Function to perform auto-save
const performAutoSave = async () => {
  console.log('⏰ Auto-save triggered')
  console.log('  - Enabled:', autoSaveSettings.value.enabled)
  console.log('  - User:', authStore.user?.username)
  console.log('  - Has unsaved changes:', composableHasUnsavedChanges.value)

  if (!autoSaveSettings.value.enabled) {
    console.log('⏰ Auto-save skipped: Not enabled')
    return
  }

  if (!authStore.user?.username) {
    console.log('⏰ Auto-save skipped: No user logged in')
    return
  }

  // Only auto-save if there are unsaved changes
  if (!composableHasUnsavedChanges.value) {
    console.log('⏰ Auto-save skipped: No unsaved changes')
    return
  }

  const autoSaveName = `${authStore.user.username}_autosave`

  try {
    console.log(`⏰ Auto-save starting: ${autoSaveName}`)
    // Check if an autosave canvas already exists
    let autosaveCanvasId: number | null = null

    // Try to find existing autosave canvas
    const canvasList = await canvasApi.getCanvases()
    const existingAutosave = canvasList.find((c: any) => c.name === autoSaveName)

    if (existingAutosave) {
      autosaveCanvasId = existingAutosave.id
      console.log(`⏰ Found existing autosave canvas with ID: ${autosaveCanvasId}`)
    } else {
      console.log('⏰ Creating new autosave canvas')
    }

    await saveCanvasData({
      name: autoSaveName,
      sharable: false,
      canvasId: autosaveCanvasId || undefined,
    })

    console.log(`⏰ Auto-save completed: ${autoSaveName}`)
  } catch (error) {
    console.error('❌ Auto-save failed:', error)
  }
}

// Function to start auto-save timer
const startAutoSaveTimer = () => {
  if (autoSaveTimer.value) {
    clearInterval(autoSaveTimer.value)
  }

  if (autoSaveSettings.value.enabled && autoSaveSettings.value.interval > 0) {
    autoSaveTimer.value = window.setInterval(
      performAutoSave,
      autoSaveSettings.value.interval * 1000
    )
    console.log(`⏰ Auto-save enabled: every ${autoSaveSettings.value.interval} seconds`)
  }
}

// Function to stop auto-save timer
const stopAutoSaveTimer = () => {
  if (autoSaveTimer.value) {
    clearInterval(autoSaveTimer.value)
    autoSaveTimer.value = null
    console.log('⏰ Auto-save disabled')
  }
}

// Watch for auto-save settings changes
watch(autoSaveSettings, (newSettings) => {
  if (newSettings.enabled) {
    startAutoSaveTimer()
  } else {
    stopAutoSaveTimer()
  }
}, { deep: true })

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

// Context menu state - now handled by useContextMenu composable

// Flag to track device right-clicks to prevent canvas menu override
const deviceRightClickInProgress = ref(false)

// Flag to track connection right-clicks to prevent canvas menu override
const connectionRightClickInProgress = ref(false)

// Connection state
const connectionStart = ref<{
  device: Device
  point: { x: number; y: number; id?: string; label?: string }
} | null>(null)

// Selected connection state
const selectedConnection = ref<number | null>(null)

// Connection port dragging state
const draggingPort = ref<{
  deviceId: number
  portId: string
} | null>(null)

// Layer visibility state
const layerVisibility = ref({
  devices: true,
  layer2: true,
  layer3: true,
  background: true,
})

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
  addArpNeighbors,
  addMacNeighbors,
  addStaticNeighbors,
  addOspfNeighbors,
  addBgpNeighbors,
} = neighborDiscoveryComposable

// Initialize modals composable
const modalState = useModals()
const {
  // Neighbor Discovery Modal
  showNeighborDiscoveryModal,
  neighborDiscoveryResult,
  closeNeighborDiscoveryModal,
  // Baseline Modal
  showBaselineExistsModal,
  baselineModalData,
  // Snapshot Modals
  showSnapshotListModal,
  showSnapshotDetailsModal,
  currentSnapshotDeviceId,
  currentSnapshotId,
  // Compare Modal
  showCompareModal,
  currentCompareDeviceId,
  // Save Canvas Modal
  saveModalRef,
  // Load Canvas Modals
  showLoadConfirmDialog,
  pendingCanvasId,
  // Autosave Restore Dialog
  showAutosaveRestoreDialog,
  autosaveCanvasId,
  hasCheckedAutosaveThisSession,
  // Duplicate Device Modal
  showDuplicateDialog,
  duplicateDeviceName,
  pendingDeviceData,
  duplicateExistingDevice,
  // Configuration Modal
  showConfigModal,
  configModalTitle,
  configModalContent,
  configModalLoading,
  currentConfigDevice,
  // Topology Modals
  showTopologyDiscoveryModal,
  showTopologyBuilderModal,
  // Device Interfaces Modal
  showInterfacesModal,
  interfacesDeviceId,
  interfacesDeviceName,
  // SSH Terminal Modal
  showSSHTerminalModal,
  sshTerminalDeviceId,
  sshTerminalDeviceName,
  // Device Overview Modal
  showDeviceOverviewModal,
  deviceOverviewId,
} = modalState

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

// Execute a command on a device
const executeCommand = async (device: Device, command: any) => {
  console.log(`🚀 Executing command on ${device.name} (${command.platform}):`)
  console.log(`Command: ${command.command}`)
  console.log(`Parser: ${command.parser}`)

  hideContextMenu()

  // Show command execution modal
  await showCommandExecution(device, command)
}

// Modal states now handled by useModals composable

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

// Connection rendering now handled by useConnectionRendering composable

// Separate shapes by layer
const backgroundShapes = computed(() => {
  return shapesStore.shapes.filter(shape => shape.layer === 'background')
})

const deviceLayerShapes = computed(() => {
  return shapesStore.shapes.filter(shape => shape.layer !== 'background')
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

// Topology Discovery functions
const openTopologyDiscovery = () => {
  showTopologyDiscoveryModal.value = true
}

const openTopologyBuilderFromDiscovery = () => {
  showTopologyDiscoveryModal.value = false
  showTopologyBuilderModal.value = true
}

// Topology Builder functions
const openTopologyBuilder = () => {
  showTopologyBuilderModal.value = true
}

const handleTopologyImport = (topology: TopologyGraph) => {
  console.log('📥 Importing topology to canvas...', topology)
  console.log('📊 Topology has:', topology.nodes?.length || 0, 'nodes and', topology.links?.length || 0, 'links')

  let newDevicesCount = 0
  let skippedDevicesCount = 0

  // Import nodes as devices (skip duplicates)
  topology.nodes.forEach(node => {
    // Check if device already exists on canvas by nautobot_id
    const existingDevice = deviceStore.devices.find(d => {
      try {
        const props = d.properties ? JSON.parse(d.properties) : {}
        return props.nautobot_id === node.device_id
      } catch {
        return false
      }
    })

    if (existingDevice) {
      console.log(`⏭️ Skipping duplicate device: ${node.device_name} (${node.device_id})`)
      skippedDevicesCount++
      return
    }

    // Create new device
    const deviceData: Omit<Device, 'id'> = {
      name: node.device_name,
      device_type: (node.device_type as 'router' | 'switch' | 'firewall' | 'vpn_gateway') || 'router',
      ip_address: node.primary_ip || '',
      position_x: node.position_x || 100,
      position_y: node.position_y || 100,
      properties: JSON.stringify({
        nautobot_id: node.device_id,
        platform: node.platform,
        ...node.metadata
      })
    }
    deviceStore.createDevice(deviceData)
    newDevicesCount++
  })

  // Import links as connections
  let newConnectionsCount = 0
  topology.links.forEach(link => {
    // Find devices by nautobot_id
    const sourceDevice = deviceStore.devices.find(d => {
      try {
        const props = d.properties ? JSON.parse(d.properties) : {}
        return props.nautobot_id === link.source_device_id
      } catch {
        return false
      }
    })

    const targetDevice = deviceStore.devices.find(d => {
      try {
        const props = d.properties ? JSON.parse(d.properties) : {}
        return props.nautobot_id === link.target_device_id
      } catch {
        return false
      }
    })

    if (sourceDevice && targetDevice) {
      // Check if connection already exists
      const existingConnection = deviceStore.connections.find(c =>
        (c.source_device_id === sourceDevice.id && c.target_device_id === targetDevice.id) ||
        (c.source_device_id === targetDevice.id && c.target_device_id === sourceDevice.id)
      )

      if (existingConnection) {
        console.log(`⏭️ Skipping duplicate connection: ${sourceDevice.name} <-> ${targetDevice.name}`)
        return
      }

      const connectionData: Omit<Connection, 'id'> = {
        source_device_id: sourceDevice.id,
        target_device_id: targetDevice.id,
        connection_type: link.link_type,
        properties: JSON.stringify({
          source_interface: link.source_interface,
          target_interface: link.target_interface,
          bidirectional: link.bidirectional,
          ...link.link_metadata
        }),
        layer: link.link_type.includes('route') ? 'layer3' : 'layer2'
      }
      deviceStore.createConnection(connectionData)
      newConnectionsCount++
    }
  })

  showTopologyBuilderModal.value = false
  console.log(`✅ Topology imported: ${newDevicesCount} new devices (${skippedDevicesCount} skipped), ${newConnectionsCount} new connections`)
}

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
  // Get the device's Nautobot ID from properties
  const props = device.properties ? JSON.parse(device.properties) : {}
  const nautobotId = props.nautobot_id

  if (!nautobotId) {
    console.error('Device does not have a Nautobot ID')
    return
  }

  deviceOverviewId.value = nautobotId
  showDeviceOverviewModal.value = true
}

const closeDeviceOverviewModal = () => {
  showDeviceOverviewModal.value = false
  deviceOverviewId.value = ''
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
        'Authorization': `Bearer ${secureStorage.getToken()}`,
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

const showDeviceInterfaces = (device: Device, _mode: 'brief' | 'full' | 'errors') => {
  // Get the device's Nautobot ID from properties
  const props = device.properties ? JSON.parse(device.properties) : {}
  const nautobotId = props.nautobot_id

  if (!nautobotId) {
    console.error('Device does not have a Nautobot ID')
    return
  }

  // For now, we'll only support "full" mode which uses the TextFSM parser
  // Brief and Errors modes could be added later with different commands or filtering
  interfacesDeviceId.value = nautobotId
  interfacesDeviceName.value = device.name
  showInterfacesModal.value = true
}

const closeInterfacesModal = () => {
  showInterfacesModal.value = false
  interfacesDeviceId.value = ''
  interfacesDeviceName.value = ''
}

const showSSHTerminal = (device: Device) => {
  // Get the device's Nautobot ID from properties
  const props = device.properties ? JSON.parse(device.properties) : {}
  const nautobotId = props.nautobot_id

  if (!nautobotId) {
    console.error('Device does not have a Nautobot ID')
    return
  }

  sshTerminalDeviceId.value = nautobotId
  sshTerminalDeviceName.value = device.name
  showSSHTerminalModal.value = true
}

const openSSHTerminalInWindow = (device: Device) => {
  // Get the device's Nautobot ID from properties
  const props = device.properties ? JSON.parse(device.properties) : {}
  const nautobotId = props.nautobot_id

  if (!nautobotId) {
    console.error('Device does not have a Nautobot ID')
    alert('Device does not have a Nautobot ID configured')
    return
  }

  // Open terminal in new window
  const terminalWindow = openTerminalWindow({
    deviceId: nautobotId,
    deviceName: device.name,
    width: 1200,
    height: 800,
  })

  if (!terminalWindow) {
    alert('Could not open terminal window. Please allow popups for this site.')
  }
}

const closeSSHTerminalModal = () => {
  showSSHTerminalModal.value = false
  sshTerminalDeviceId.value = ''
  sshTerminalDeviceName.value = ''
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

// Baseline management functions
const createBaseline = async (device: Device) => {
  try {
    console.log('Creating baseline for device:', device.name, device.id)

    // Check if baseline already exists
    const token = secureStorage.getToken()
    if (!token) {
      alert('Not authenticated')
      return
    }

    // Get Nautobot UUID from device properties
    const deviceProps = device.properties ? JSON.parse(device.properties) : {}
    const nautobotId = deviceProps.nautobot_id

    if (!nautobotId) {
      alert(`Device ${device.name} does not have a Nautobot ID. Cannot create baseline.`)
      return
    }

    // Check for existing baseline using Nautobot UUID
    const checkResponse = await fetch(`/api/snapshots/check?device_id=${nautobotId}&type=baseline`, {
      headers: {
        'Authorization': `Bearer ${token}`,
      },
    })

    if (!checkResponse.ok) {
      throw new Error(`Failed to check for existing baseline: ${checkResponse.status} ${checkResponse.statusText}`)
    }

    const checkData = await checkResponse.json()

    if (checkData.exists) {
      // Baseline exists - show modal
      baselineModalData.value = {
        device: device,
        baselineData: checkData
      }
      showBaselineExistsModal.value = true
    } else {
      // No baseline exists - create new
      await scheduleBaselineCreation(device, 'Initial baseline')
    }

  } catch (error) {
    console.error('Error creating baseline:', error)
    alert(`Failed to create baseline: ${error}`)
  }
}

const handleBaselineOverwrite = async () => {
  if (baselineModalData.value.device) {
    await scheduleBaselineCreation(baselineModalData.value.device, 'Baseline update - overwrite')
  }
}

const scheduleBaselineCreation = async (device: Device, notes: string) => {
  try {
    const token = secureStorage.getToken()
    if (!token) return

    // Get Nautobot UUID from device properties
    const deviceProps = device.properties ? JSON.parse(device.properties) : {}
    const nautobotId = deviceProps.nautobot_id

    if (!nautobotId) {
      alert(`Device ${device.name} does not have a Nautobot ID. Cannot create baseline.`)
      return
    }

    const requestBody = {
      device_ids: [nautobotId],  // Use Nautobot UUID
      notes: notes,
    }

    console.log('🔍 Sending baseline request:', requestBody)
    console.log('🔍 Nautobot ID:', nautobotId)
    console.log('🔍 Notes:', notes)

    // Schedule baseline creation task
    const response = await fetch(`/api/settings/jobs/baseline`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${token}`,
      },
      body: JSON.stringify(requestBody),
    })

    console.log('🔍 Response status:', response.status)

    if (!response.ok) {
      const errorText = await response.text()
      console.error('🔍 Error response:', errorText)
      throw new Error(`Failed to schedule baseline creation: ${response.status} - ${errorText}`)
    }

    const result = await response.json()
    console.log('Baseline creation scheduled:', result)
    alert(`Baseline creation scheduled for ${device.name}\nTask ID: ${result.task_id}`)
  } catch (error) {
    console.error('Error scheduling baseline:', error)
    throw error
  }
}

// Snapshot management functions
const createSnapshot = async (device: Device) => {
  try {
    console.log('Creating snapshot for device:', device.name, device.id)

    const token = secureStorage.getToken()
    if (!token) {
      alert('Not authenticated')
      return
    }

    // Get Nautobot UUID from device properties
    const deviceProps = device.properties ? JSON.parse(device.properties) : {}
    const nautobotId = deviceProps.nautobot_id

    if (!nautobotId) {
      alert(`Device ${device.name} does not have a Nautobot ID. Cannot create snapshot.`)
      return
    }

    // Create snapshot directly without checking if one exists
    await scheduleSnapshotCreation(device, `Snapshot created on ${new Date().toLocaleString()}`)

  } catch (error) {
    console.error('Error creating snapshot:', error)
    alert(`Failed to create snapshot: ${error}`)
  }
}

const scheduleSnapshotCreation = async (device: Device, notes: string) => {
  try {
    const token = secureStorage.getToken()
    if (!token) return

    // Get Nautobot UUID from device properties
    const deviceProps = device.properties ? JSON.parse(device.properties) : {}
    const nautobotId = deviceProps.nautobot_id

    if (!nautobotId) {
      alert(`Device ${device.name} does not have a Nautobot ID. Cannot create snapshot.`)
      return
    }

    const requestBody = {
      device_ids: [nautobotId],
      notes: notes,
    }

    console.log('🔍 Sending snapshot request:', requestBody)

    // Schedule snapshot creation task (using the snapshot endpoint, not baseline)
    const response = await fetch(`/api/settings/jobs/snapshot`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${token}`,
      },
      body: JSON.stringify(requestBody),
    })

    console.log('🔍 Response status:', response.status)

    if (!response.ok) {
      const errorText = await response.text()
      console.error('🔍 Error response:', errorText)
      throw new Error(`Failed to schedule snapshot creation: ${response.status} - ${errorText}`)
    }

    const result = await response.json()
    console.log('Snapshot creation scheduled:', result)
    alert(`Snapshot creation scheduled for ${device.name}\nTask ID: ${result.task_id}`)
  } catch (error) {
    console.error('Error scheduling snapshot:', error)
    throw error
  }
}

const manageSnapshots = (device: Device) => {
  console.log('Managing snapshots for device:', device.name, device.id)

  // Get Nautobot UUID from device properties
  const deviceProps = device.properties ? JSON.parse(device.properties) : {}
  const nautobotId = deviceProps.nautobot_id

  if (!nautobotId) {
    alert(`Device ${device.name} does not have a Nautobot ID. Cannot manage snapshots.`)
    return
  }

  currentSnapshotDeviceId.value = nautobotId
  showSnapshotListModal.value = true
}

const handleShowSnapshotDetails = (snapshotId: number) => {
  currentSnapshotId.value = snapshotId
  showSnapshotDetailsModal.value = true
}

const compareSnapshotToBaseline = (device: Device) => {
  console.log('Opening compare modal for device:', device.name, device.id)

  // Get Nautobot UUID from device properties
  const deviceProps = device.properties ? JSON.parse(device.properties) : {}
  const nautobotId = deviceProps.nautobot_id

  if (!nautobotId) {
    alert(`Device ${device.name} does not have a Nautobot ID. Cannot compare.`)
    return
  }

  currentCompareDeviceId.value = nautobotId
  showCompareModal.value = true
}

const compareBaseline = async (device: Device) => {
  try {
    console.log('Comparing baseline for device:', device.name, device.id)

    const token = secureStorage.getToken()
    if (!token) {
      alert('Not authenticated')
      return
    }

    // Get Nautobot UUID from device properties
    const deviceProps = device.properties ? JSON.parse(device.properties) : {}
    const nautobotId = deviceProps.nautobot_id

    if (!nautobotId) {
      alert(`Device ${device.name} does not have a Nautobot ID. Cannot compare baseline.`)
      return
    }

    // Check if baseline exists using Nautobot UUID
    const checkResponse = await fetch(`/api/snapshots/check?device_id=${nautobotId}&type=baseline`, {
      headers: {
        'Authorization': `Bearer ${token}`,
      },
    })

    if (!checkResponse.ok) {
      throw new Error(`Failed to check for baseline: ${checkResponse.status} ${checkResponse.statusText}`)
    }

    const checkData = await checkResponse.json()

    if (!checkData.exists) {
      alert(`No baseline exists for ${device.name}.\n\nPlease create a baseline first.`)
      return
    }

    // TODO: Implement comparison view
    alert(
      `Baseline comparison for ${device.name}\n\n` +
      `Baseline found:\n` +
      `Created: ${new Date(checkData.created_at).toLocaleString()}\n` +
      `Version: ${checkData.version}\n` +
      `Commands: ${checkData.command_count || 'N/A'}\n\n` +
      `Comparison view coming soon!`
    )

  } catch (error) {
    console.error('Error comparing baseline:', error)
    alert(`Failed to compare baseline: ${error}`)
  }
}

// Manage connection ports on a device
const manageConnectionPorts = (device: Device) => {
  const currentPorts = device.connectionPorts || []
  
  let portsText = `Manage Connection Ports for ${device.name}\n\n`
  portsText += `Current ports:\n`
  
  if (currentPorts.length === 0) {
    portsText += `  (No custom ports defined - using default edges)\n`
  } else {
    currentPorts.forEach((port, index) => {
      portsText += `  ${index + 1}. ${port.label || port.id} at (${port.x}, ${port.y})\n`
    })
  }
  
  portsText += `\nActions:\n`
  portsText += `1. Add a new port\n`
  portsText += `2. Remove a port\n`
  portsText += `3. Clear all ports\n`
  portsText += `4. Cancel\n\n`
  portsText += `Enter choice (1-4):`
  
  const choice = prompt(portsText)
  
  if (choice === '1') {
    // Add a new port
    const x = prompt('Enter X position (0-60):', '30')
    const y = prompt('Enter Y position (0-60):', '0')
    const label = prompt('Enter port label (optional):', '')
    
    if (x !== null && y !== null) {
      const newPort = {
        id: `port-${Date.now()}`,
        x: Number(x),
        y: Number(y),
        label: label || undefined
      }
      
      const updatedPorts = [...currentPorts, newPort]
      deviceStore.updateDevice(device.id, {
        connectionPorts: updatedPorts
      })
      
      console.log('✅ Port added:', newPort)
      alert(`Port added at (${x}, ${y})`)
    }
  } else if (choice === '2') {
    // Remove a port
    if (currentPorts.length === 0) {
      alert('No ports to remove')
      return
    }
    
    const indexStr = prompt(`Enter port number to remove (1-${currentPorts.length}):`)
    if (indexStr !== null) {
      const index = Number(indexStr) - 1
      if (index >= 0 && index < currentPorts.length) {
        const updatedPorts = currentPorts.filter((_, i) => i !== index)
        deviceStore.updateDevice(device.id, {
          connectionPorts: updatedPorts
        })
        
        console.log('✅ Port removed')
        alert('Port removed successfully')
      }
    }
  } else if (choice === '3') {
    // Clear all ports
    if (confirm('Remove all custom connection ports?')) {
      deviceStore.updateDevice(device.id, {
        connectionPorts: []
      })
      
      console.log('✅ All ports cleared')
      alert('All ports cleared')
    }
  }
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
  }

  hideContextMenu()
}

// eslint-disable-next-line @typescript-eslint/no-unused-vars
const getConnectionPoints = (device: Device) => {
  // If device has custom connection ports, return those
  if (device.connectionPorts && device.connectionPorts.length > 0) {
    return device.connectionPorts.map(port => ({
      id: port.id,
      x: port.x,
      y: port.y,
      label: port.label
    }))
  }
  
  // Otherwise return default connection points
  return [
    { x: 0, y: DEVICE_HALF_SIZE }, // Left (middle of device height)
    { x: DEVICE_SIZE, y: DEVICE_HALF_SIZE }, // Right (middle of device height)
    { x: DEVICE_HALF_SIZE, y: 0 }, // Top (middle of device width)
    { x: DEVICE_HALF_SIZE, y: DEVICE_SIZE }, // Bottom (middle of device width)
  ]
}

// getEdgeConnectionPoint now handled by useConnectionRendering composable

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
          layer: symbol.layer || 'background', // Default to background layer
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

  // Handle Alt+Click to add connection port at click position
  if (event.evt?.altKey && connectionMode.value) {
    const stage = event.target.getStage()
    const pointerPosition = stage.getPointerPosition()
    
    if (pointerPosition) {
      // Convert stage coordinates to device-relative coordinates
      const deviceRelativeX = (pointerPosition.x - position.value.x) / scale.value - device.position_x
      const deviceRelativeY = (pointerPosition.y - position.value.y) / scale.value - device.position_y
      
      // Clamp to device bounds (0 to DEVICE_SIZE)
      const clampedX = Math.max(0, Math.min(DEVICE_SIZE, deviceRelativeX))
      const clampedY = Math.max(0, Math.min(DEVICE_SIZE, deviceRelativeY))
      
      // Add the new port
      const currentPorts = device.connectionPorts || []
      const newPort = {
        id: `port-${Date.now()}`,
        x: Math.round(clampedX),
        y: Math.round(clampedY),
        label: `P${currentPorts.length + 1}`
      }
      
      const updatedPorts = [...currentPorts, newPort]
      deviceStore.updateDevice(device.id, {
        connectionPorts: updatedPorts
      })
      
      console.log('✅ Port added via Alt+Click:', newPort, 'at device position:', device.position_x, device.position_y)
    }
    
    return // Don't process normal selection when Alt+Click
  }

  // Deselect any selected connection when clicking a device (unless shift is held)
  if (!event.evt?.shiftKey && selectedConnection.value !== null) {
    selectedConnection.value = null
  }

  // Only clear shape selection if not holding Shift (for cross-selection)
  if (!event.evt?.shiftKey) {
    clearShapeSelection()
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
  }
}

// Track which device is currently being dragged and its initial position
const dragState = ref<{
  draggedDevice: Device | null
  initialPositions: Map<number, { x: number; y: number }>
  initialShapePositions?: Map<number, { x: number; y: number }>
} | null>(null)

// Track real-time positions of devices during drag for connection rendering
const dragPositions = ref<Map<number, { x: number; y: number }>>(new Map())

// Initialize connection rendering composable (must be after dragPositions)
const connectionRendering = useConnectionRendering({
  connections: deviceStore.connections,
  devices: deviceStore.devices,
  dragPositions,
})
const {
  draggingWaypoint,
  renderConnections,
  layer2Connections,
  layer3Connections,
  isLayer2Connection,
  isLayer3Connection,
  getEdgeConnectionPoint,
  calculateOrthogonalPath,
  getConnectionWaypoints,
  onWaypointDragStart,
  onWaypointDragMove,
  onWaypointDragEnd,
  onWaypointRightClick,
  deleteWaypoint,
} = connectionRendering

const onDeviceDragStart = (device: Device) => {
  // Don't start device drag if we're dragging a port
  if (draggingPort.value !== null) {
    console.log('🚫 Preventing device drag - port is being dragged')
    return false
  }
  
  // Initialize drag state
  dragState.value = {
    draggedDevice: device,
    initialPositions: new Map(),
    initialShapePositions: new Map()
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

  // Store initial positions of all selected shapes
  const selectedShapesList = Array.from(selectedShapes.value)
    .map(id => shapesStore.shapes.find(s => s.id === id))
    .filter((s): s is any => s !== undefined)

  selectedShapesList.forEach(selectedShape => {
    dragState.value!.initialShapePositions!.set(selectedShape.id, {
      x: selectedShape.position_x,
      y: selectedShape.position_y
    })
  })
}

const onDeviceDragMove = (device: Device, event: any) => {
  const currentX = event.target.x()
  const currentY = event.target.y()

  // Update drag position for the dragged device for real-time connection rendering
  dragPositions.value.set(device.id, { x: currentX, y: currentY })

  // Handle multi-selection dragging (devices and shapes)
  if (dragState.value) {
    // Calculate the delta from the device's initial position
    const initialPos = dragState.value.initialPositions.get(device.id)
    if (!initialPos) return

    const deltaX = currentX - initialPos.x
    const deltaY = currentY - initialPos.y

    // Update positions of other selected devices in real-time in the store
    if (selectedDevices.value.size > 1 && selectedDevices.value.has(device.id)) {
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
        deviceStore.updateDevice(selectedDevice.id, {
          position_x: newX,
          position_y: newY,
        })
      })
    }

    // Update positions of selected shapes in real-time
    if (selectedShapes.value.size > 0 && dragState.value.initialShapePositions) {
      const selectedShapesList = Array.from(selectedShapes.value)
        .map(id => shapesStore.shapes.find(s => s.id === id))
        .filter((s): s is any => s !== undefined)

      selectedShapesList.forEach(selectedShape => {
        const initialShapePos = dragState.value!.initialShapePositions!.get(selectedShape.id)
        if (!initialShapePos) return

        const newX = initialShapePos.x + deltaX
        const newY = initialShapePos.y + deltaY

        // Update the shape position in the store in real-time
        shapesStore.updateShape(selectedShape.id, {
          position_x: newX,
          position_y: newY,
        })
      })
    }
  }
}

const onDeviceDragEnd = (device: Device, event: any) => {
  let newX = event.target.x()
  let newY = event.target.y()

  // Apply snap-to-grid if enabled
  if (snapToGrid.value) {
    const snapped = snapToGridCoordinates(newX, newY)
    newX = snapped.x
    newY = snapped.y
    // Update the visual position immediately
    event.target.x(newX)
    event.target.y(newY)
  }

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
  // Only clear device selection if not holding Shift (for cross-selection)
  if (!event.evt?.shiftKey) {
    selectedDevice.value = null
    selectedDevices.value.clear()
  }
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

  // Check if Alt/Option key is pressed - add waypoint at click position
  if (event.evt?.altKey && selectedConnection.value === connection.id) {
    addWaypointAtPosition(connection.id, event)
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

const toggleConnectionRoutingStyle = (connectionId: number) => {
  const connection = deviceStore.connections.find(c => c.id === connectionId)
  if (!connection) return

  // Toggle between straight and orthogonal
  const currentStyle = connection.routing_style || 'straight'
  connection.routing_style = currentStyle === 'straight' ? 'orthogonal' : 'straight'

  console.log('✅ Connection routing style changed to:', connection.routing_style)
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

const clearConnectionWaypoints = (connectionId: number) => {
  const connection = deviceStore.connections.find(c => c.id === connectionId)
  if (!connection) return

  connection.waypoints = []
  console.log('✅ Waypoints cleared for connection:', connectionId)
}

// Waypoint management now handled by useConnectionRendering composable

const addWaypointAtPosition = (connectionId: number, event: any) => {
  const connection = deviceStore.connections.find(c => c.id === connectionId)
  if (!connection) return

  const stage = event.target.getStage()
  const pointerPosition = stage.getPointerPosition()

  if (!pointerPosition) return

  // Convert stage coordinates to world coordinates (accounting for zoom/pan)
  const worldX = (pointerPosition.x - position.value.x) / scale.value
  const worldY = (pointerPosition.y - position.value.y) / scale.value

  // Initialize waypoints array if it doesn't exist
  if (!connection.waypoints) {
    connection.waypoints = []
  }

  // Find the closest segment to insert the waypoint
  const points = renderConnections.value.find(c => c.id === connectionId)?.points || []
  let closestSegmentIndex = 0
  let minDistance = Infinity

  // Find which segment the click is closest to
  for (let i = 0; i < points.length - 2; i += 2) {
    const x1 = points[i]
    const y1 = points[i + 1]
    const x2 = points[i + 2]
    const y2 = points[i + 3]

    // Calculate distance from point to line segment
    const distance = distanceToSegment(worldX, worldY, x1, y1, x2, y2)
    if (distance < minDistance) {
      minDistance = distance
      closestSegmentIndex = i / 2
    }
  }

  // Insert waypoint at the appropriate position
  connection.waypoints.splice(closestSegmentIndex, 0, {
    x: worldX,
    y: worldY
  })

  console.log('✅ Waypoint added at:', { x: worldX, y: worldY }, 'segment:', closestSegmentIndex)
}

// Helper function to calculate distance from point to line segment
const distanceToSegment = (px: number, py: number, x1: number, y1: number, x2: number, y2: number): number => {
  const dx = x2 - x1
  const dy = y2 - y1
  const lengthSquared = dx * dx + dy * dy

  if (lengthSquared === 0) {
    // Line segment is a point
    return Math.sqrt((px - x1) ** 2 + (py - y1) ** 2)
  }

  // Calculate projection of point onto line
  let t = ((px - x1) * dx + (py - y1) * dy) / lengthSquared
  t = Math.max(0, Math.min(1, t))

  const projX = x1 + t * dx
  const projY = y1 + t * dy

  return Math.sqrt((px - projX) ** 2 + (py - projY) ** 2)
}

const onConnectionPointClick = (device: Device, point: { x: number; y: number; id?: string }, event: any) => {
  event.cancelBubble = true

  if (!connectionMode.value) return

  if (!connectionStart.value) {
    connectionStart.value = { device, point }
  } else {
    if (connectionStart.value.device.id !== device.id) {
      try {
        // Create connection with port IDs if available
        deviceStore.createConnection({
          source_device_id: connectionStart.value.device.id,
          target_device_id: device.id,
          connection_type: 'ethernet',
          source_port_id: connectionStart.value.point.id,
          target_port_id: point.id,
        })
      } catch (error) {
        console.error('Failed to create connection:', error)
      }
    }
    connectionStart.value = null
    connectionMode.value = false
  }
}

// Right-click on connection point to delete custom port
const onConnectionPointRightClick = (device: Device, point: { x: number; y: number; id?: string; label?: string }, event: any) => {
  event.evt.preventDefault()
  event.evt.stopPropagation()
  event.cancelBubble = true

  // Only allow deleting custom ports (those with an id and label)
  if (!point.id || !point.label) {
    console.log('Cannot delete default edge connection points')
    return
  }

  if (confirm(`Delete connection port "${point.label}"?`)) {
    const currentPorts = device.connectionPorts || []
    const updatedPorts = currentPorts.filter(p => p.id !== point.id)
    
    deviceStore.updateDevice(device.id, {
      connectionPorts: updatedPorts
    })
    
    console.log('✅ Port deleted via right-click:', point.label)
  }
}

// Connection port drag handlers
const onConnectionPortDragStart = (device: Device, point: { x: number; y: number; id?: string; label?: string }, event: any) => {
  // Only allow dragging custom ports
  if (!point.id || !point.label) {
    event.cancelBubble = true
    return false
  }
  
  // Stop event from propagating to device group
  event.cancelBubble = true
  
  // Set dragging port state to prevent device dragging
  draggingPort.value = {
    deviceId: device.id,
    portId: point.id
  }
  
  console.log('🎯 Port drag start:', point.label)
}

const onConnectionPortDragMove = (device: Device, point: { x: number; y: number; id?: string; label?: string }, event: any) => {
  // Only allow dragging custom ports
  if (!point.id || !point.label) {
    return
  }

  // Stop event from propagating to device group
  event.cancelBubble = true

  // Get the dragged node's position (relative to device group)
  const node = event.target
  const nodeX = node.x()
  const nodeY = node.y()
  
  // Clamp to device bounds
  const clampedX = Math.max(0, Math.min(DEVICE_SIZE, nodeX))
  const clampedY = Math.max(0, Math.min(DEVICE_SIZE, nodeY))
  
  // Update node position to clamped values
  node.x(clampedX)
  node.y(clampedY)
  
  // Update the port in the device's connectionPorts array
  const currentPorts = device.connectionPorts || []
  const portIndex = currentPorts.findIndex(p => p.id === point.id)
  
  if (portIndex !== -1) {
    currentPorts[portIndex] = {
      ...currentPorts[portIndex],
      x: Math.round(clampedX),
      y: Math.round(clampedY)
    }
    
    // Update device (this will trigger reactivity)
    deviceStore.updateDevice(device.id, {
      connectionPorts: [...currentPorts]
    })
  }
}

const onConnectionPortDragEnd = (device: Device, point: { x: number; y: number; id?: string; label?: string }, event: any) => {
  // Only allow dragging custom ports
  if (!point.id || !point.label) {
    return
  }
  
  // Stop event from propagating to device group (critical!)
  event.cancelBubble = true
  
  const node = event.target
  const finalX = Math.round(node.x())
  const finalY = Math.round(node.y())
  
  console.log('✅ Port drag end:', point.label, 'final position:', finalX, finalY)
  
  // Clear dragging port state
  draggingPort.value = null
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

// Context menu items - using composable (must be after all function declarations)
const contextMenuItems = useContextMenuItems({
  contextMenu,
  hideContextMenu,
  selectedDevices,
  selectedShapes,
  layerVisibility,
  deviceStore,
  canvasContainer,
  // Shape operations
  openShapeColorModal,
  alignShapesHorizontally,
  alignShapesVertically,
  deleteShape,
  deleteMultiShapes,
  // Connection operations
  showConnectionInfo,
  showConnectionStatus,
  showConnectionStats,
  toggleConnectionRoutingStyle,
  clearConnectionWaypoints,
  deleteConnection,
  // Canvas operations
  fitToScreen,
  resetView,
  openTopologyDiscovery,
  openTopologyBuilder,
  loadCanvas,
  saveCanvas,
  saveCanvasAs,
  clearCanvas,
  // Multi-device operations
  showMultiDeviceConfig,
  showMultiDeviceChanges,
  showMultiDeviceNeighbors,
  addMultiDeviceNeighborsToCanvas,
  connectTwoDevices,
  analyzeMultiDevices,
  alignDevicesHorizontally,
  alignDevicesVertically,
  deleteMultiDevices,
  // Single device operations
  showDeviceOverview,
  showSSHTerminal,
  openSSHTerminalInWindow,
  showDeviceRunningConfig,
  showDeviceStartupConfig,
  showDeviceChanges,
  showDeviceInterfaces,
  executeCommand,
  reloadCommands,
  showNeighbors,
  addCdpNeighbors,
  addMacNeighbors,
  addArpNeighbors,
  addStaticNeighbors,
  addOspfNeighbors,
  addBgpNeighbors,
  createBaseline,
  createSnapshot,
  manageSnapshots,
  compareSnapshotToBaseline,
  manageConnectionPorts,
  deleteDevice,
  getDevicePlatform,
  getCommandsForPlatform,
})

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

  // Don't interfere with clicks inside modals
  const clickedElement = event.target as HTMLElement
  const clickedInsideModal = clickedElement.closest('[data-modal="true"]')
  if (clickedInsideModal) {
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
    }
  }
}

// Global keyboard handler for shortcuts
const handleGlobalKeyDown = (event: KeyboardEvent) => {
  // Handle Ctrl+S (or Cmd+S on Mac) for save
  if ((event.ctrlKey || event.metaKey) && event.key === 's') {
    event.preventDefault() // Prevent browser's default save behavior
    saveCanvas()
    return
  }

  // Handle arrow keys for moving selected devices
  if (['ArrowUp', 'ArrowDown', 'ArrowLeft', 'ArrowRight'].includes(event.key)) {
    // Check if any device is selected
    if (selectedDevice.value || selectedDevices.value.size > 0) {
      event.preventDefault() // Prevent page scrolling
      
      // Determine move distance (10px normal, 50px with Shift for grid alignment)
      const moveDistance = event.shiftKey ? GRID_SIZE : 10
      
      // Calculate offset based on arrow key
      let dx = 0
      let dy = 0
      
      switch (event.key) {
        case 'ArrowUp':
          dy = -moveDistance
          break
        case 'ArrowDown':
          dy = moveDistance
          break
        case 'ArrowLeft':
          dx = -moveDistance
          break
        case 'ArrowRight':
          dx = moveDistance
          break
      }
      
      // Move the selected device(s)
      if (selectedDevices.value.size > 0) {
        // Move all selected devices
        selectedDevices.value.forEach(deviceId => {
          const device = deviceStore.devices.find(d => d.id === deviceId)
          if (device) {
            let newX = device.position_x + dx
            let newY = device.position_y + dy
            
            // Apply snap-to-grid if enabled
            if (snapToGrid.value) {
              const snapped = snapToGridCoordinates(newX, newY)
              newX = snapped.x
              newY = snapped.y
            }
            
            deviceStore.updateDevice(device.id, {
              position_x: newX,
              position_y: newY,
            })
          }
        })
        console.log(`⌨️ Moved ${selectedDevices.value.size} device(s) by (${dx}, ${dy})`)
      } else if (selectedDevice.value) {
        // Move single selected device
        let newX = selectedDevice.value.position_x + dx
        let newY = selectedDevice.value.position_y + dy
        
        // Apply snap-to-grid if enabled
        if (snapToGrid.value) {
          const snapped = snapToGridCoordinates(newX, newY)
          newX = snapped.x
          newY = snapped.y
        }
        
        deviceStore.updateDevice(selectedDevice.value.id, {
          position_x: newX,
          position_y: newY,
        })
        console.log(`⌨️ Moved device "${selectedDevice.value.name}" by (${dx}, ${dy})`)
      }
    }
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

// Handlers for autosave restore dialog
const handleAutosaveRestore = async () => {
  showAutosaveRestoreDialog.value = false
  if (autosaveCanvasId.value) {
    await loadCanvasById(autosaveCanvasId.value)
    autosaveCanvasId.value = null
  }
}

const handleAutosaveDiscard = async () => {
  showAutosaveRestoreDialog.value = false

  // Delete the autosave canvas
  if (autosaveCanvasId.value && authStore.user?.username) {
    try {
      await canvasApi.deleteCanvas(autosaveCanvasId.value)
      console.log('🗑️ Auto-save canvas deleted')
    } catch (error) {
      console.error('❌ Failed to delete auto-save canvas:', error)
    }
    autosaveCanvasId.value = null
  }
}

// Function to check for autosave on startup
const checkForAutosave = async () => {
  // Only check once per session - don't prompt again when navigating back to Dashboard
  // Use sessionStorage to persist across component remounts
  const sessionKey = 'noc_canvas_autosave_checked'
  if (hasCheckedAutosaveThisSession.value || sessionStorage.getItem(sessionKey)) {
    return
  }

  if (!authStore.user?.username) {
    return
  }

  const autoSaveName = `${authStore.user.username}_autosave`

  try {
    const canvasList = await canvasApi.getCanvases()
    const existingAutosave = canvasList.find((c: any) => c.name === autoSaveName)

    if (existingAutosave) {
      autosaveCanvasId.value = existingAutosave.id
      showAutosaveRestoreDialog.value = true
      console.log('💾 Auto-save found:', autoSaveName)
    }

    // Mark that we've checked for autosave this session
    hasCheckedAutosaveThisSession.value = true
    sessionStorage.setItem(sessionKey, 'true')
  } catch (error) {
    console.error('❌ Failed to check for auto-save:', error)
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

  // Load auto-save settings from backend
  try {
    const response = await makeAuthenticatedRequest('/api/settings/unified')
    if (response.ok) {
      const data = await response.json()
      if (data.canvas) {
        autoSaveSettings.value = {
          enabled: data.canvas.autoSaveEnabled || false,
          interval: data.canvas.autoSaveInterval || 60,
        }
        console.log('⏰ Auto-save settings loaded:', autoSaveSettings.value)

        // Start auto-save timer if enabled
        if (autoSaveSettings.value.enabled) {
          startAutoSaveTimer()
        }
      }
    }
  } catch (error) {
    console.error('Failed to load auto-save settings:', error)
  }

  // Check for existing autosave
  await checkForAutosave()

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
  // Clean up auto-save timer
  stopAutoSaveTimer()

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
