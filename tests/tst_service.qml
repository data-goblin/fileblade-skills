import QtQuick
import QtTest
import ".." as Skills

TestCase {
  name: "SkillsProviderService"
  Item { id: files }
  Component { id: providerComponent; Skills.Service { manifest: ({ id: "test.skills", __sourceDir: "/plugins/skills" }) } }

  function test_cold_load_and_shared_observers() {
    var provider = createTemporaryObject(providerComponent, this)
    var view = { service: function() { return files }, ui: { url: function(name) {
      compare(name, "ArtifactInventory")
      return Qt.resolvedUrl("InventoryProbe.qml")
    } } }
    compare(provider.inventory, null)
    provider.attach(view)
    verify(provider.inventory !== null)
    compare(provider.inventory.files, files)
    compare(provider.inventory.providerId, "test.skills")
    compare(provider.inventory.providerRoot, "/plugins/skills")
    compare(provider.inventory.maximumItems, 256)
    var inventory = provider.inventory
    provider.attach(view)
    compare(provider.inventory.observers.length, 1)
    var second = { ui: view.ui, service: view.service }
    provider.attach(second)
    compare(provider.inventory.observers.length, 2)
    provider.detach(view)
    compare(provider.inventory.observers.length, 1)
    provider.detach(second)
    compare(provider.inventory.observers.length, 0)
    provider.attach(view)
    compare(provider.inventory, inventory)
    compare(provider.inventory.observers.length, 1)
  }
}
