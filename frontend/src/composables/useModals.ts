import { ref, type Ref } from 'vue'
import type { Device } from '@/stores/devices'
import type { NeighborDiscoveryResult } from './useNeighborDiscovery'

export interface ModalState {
  // Neighbor Discovery Modal
  showNeighborDiscoveryModal: Ref<boolean>
  neighborDiscoveryResult: Ref<NeighborDiscoveryResult | null>
  closeNeighborDiscoveryModal: () => void

  // Baseline Modal
  showBaselineExistsModal: Ref<boolean>
  baselineModalData: Ref<{
    device: Device | null
    baselineData: any
  }>

  // Snapshot Modals
  showSnapshotListModal: Ref<boolean>
  showSnapshotDetailsModal: Ref<boolean>
  currentSnapshotDeviceId: Ref<string | null>
  currentSnapshotId: Ref<number | null>

  // Compare Modal
  showCompareModal: Ref<boolean>
  currentCompareDeviceId: Ref<string | null>

  // Save Canvas Modal
  saveModalRef: Ref<any>

  // Load Canvas Modals
  showLoadConfirmDialog: Ref<boolean>
  pendingCanvasId: Ref<number | null>

  // Autosave Restore Dialog
  showAutosaveRestoreDialog: Ref<boolean>
  autosaveCanvasId: Ref<number | null>
  hasCheckedAutosaveThisSession: Ref<boolean>

  // Duplicate Device Modal
  showDuplicateDialog: Ref<boolean>
  duplicateDeviceName: Ref<string>
  pendingDeviceData: Ref<any>
  duplicateExistingDevice: Ref<Device | null>

  // Configuration Modal
  showConfigModal: Ref<boolean>
  configModalTitle: Ref<string>
  configModalContent: Ref<string>
  configModalLoading: Ref<boolean>
  currentConfigDevice: Ref<Device | null>

  // Topology Modals
  showTopologyDiscoveryModal: Ref<boolean>
  showTopologyBuilderModal: Ref<boolean>

  // Device Interfaces Modal
  showInterfacesModal: Ref<boolean>
  interfacesDeviceId: Ref<string>
  interfacesDeviceName: Ref<string>

  // SSH Terminal Modal
  showSSHTerminalModal: Ref<boolean>
  sshTerminalDeviceId: Ref<string>
  sshTerminalDeviceName: Ref<string>

  // Device Overview Modal
  showDeviceOverviewModal: Ref<boolean>
  deviceOverviewId: Ref<string>
}

export function useModals(): ModalState {
  // Neighbor Discovery Modal state
  const showNeighborDiscoveryModal = ref(false)
  const neighborDiscoveryResult = ref<NeighborDiscoveryResult | null>(null)

  const closeNeighborDiscoveryModal = () => {
    showNeighborDiscoveryModal.value = false
    neighborDiscoveryResult.value = null
  }

  // Baseline modal state
  const showBaselineExistsModal = ref(false)
  const baselineModalData = ref<{
    device: Device | null
    baselineData: any
  }>({
    device: null,
    baselineData: null
  })

  // Snapshot modal state
  const showSnapshotListModal = ref(false)
  const showSnapshotDetailsModal = ref(false)
  const currentSnapshotDeviceId = ref<string | null>(null)
  const currentSnapshotId = ref<number | null>(null)

  // Compare modal state
  const showCompareModal = ref(false)
  const currentCompareDeviceId = ref<string | null>(null)

  // Save Canvas Modal state
  const saveModalRef = ref()

  // Load Canvas Modal state
  const showLoadConfirmDialog = ref(false)
  const pendingCanvasId = ref<number | null>(null)

  // Auto-save restore dialog state
  const showAutosaveRestoreDialog = ref(false)
  const autosaveCanvasId = ref<number | null>(null)
  const hasCheckedAutosaveThisSession = ref(false)

  // Duplicate Device Modal state
  const showDuplicateDialog = ref(false)
  const duplicateDeviceName = ref('')
  const pendingDeviceData = ref<any>(null)
  const duplicateExistingDevice = ref<Device | null>(null)

  // Device Configuration Modal state
  const showConfigModal = ref(false)
  const configModalTitle = ref('')
  const configModalContent = ref('')
  const configModalLoading = ref(false)
  const currentConfigDevice = ref<Device | null>(null)

  // Topology Discovery Modal state
  const showTopologyDiscoveryModal = ref(false)

  // Topology Builder Modal state
  const showTopologyBuilderModal = ref(false)

  // Device Interfaces Modal state
  const showInterfacesModal = ref(false)
  const interfacesDeviceId = ref('')
  const interfacesDeviceName = ref('')

  // SSH Terminal Modal state
  const showSSHTerminalModal = ref(false)
  const sshTerminalDeviceId = ref('')
  const sshTerminalDeviceName = ref('')

  // Device Overview Modal state
  const showDeviceOverviewModal = ref(false)
  const deviceOverviewId = ref('')

  return {
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
  }
}
