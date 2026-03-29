<script lang="ts">
  import type { Sync3DCompareProps, Sync3DCompareEvents } from "./types";
  import { Gradio } from "@gradio/utils";
  import { Block } from "@gradio/atoms";
  import { StatusTracker } from "@gradio/statustracker";
  import Sync3DCompare from "./shared/Sync3DCompare.svelte";

  const props = $props();
  // svelte-ignore state_referenced_locally
  const gradio = new Gradio<Sync3DCompareEvents, Sync3DCompareProps>(props);
</script>

<Block
  visible={gradio.shared.visible}
  elem_id={gradio.shared.elem_id}
  elem_classes={gradio.shared.elem_classes}
  container={true}
  scale={gradio.shared.scale}
  min_width={gradio.shared.min_width}
>
  {#if gradio.shared.loading_status}
    <StatusTracker
      autoscroll={gradio.shared.autoscroll}
      i18n={gradio.i18n}
      {...gradio.shared.loading_status}
      on_clear_status={() =>
        gradio.dispatch("clear_status", gradio.shared.loading_status)}
    />
  {/if}

  <Sync3DCompare
    value={gradio.props.value}
    render_mode={gradio.props.render_mode}
    sync_camera={gradio.props.sync_camera}
    point_size_mode={gradio.props.point_size_mode}
    point_size={gradio.props.point_size}
    max_point_size={gradio.props.max_point_size}
    height={gradio.props.height}
    max_views={gradio.props.max_views}
    default_zoom={gradio.props.default_zoom}
    min_zoom={gradio.props.min_zoom}
    max_zoom={gradio.props.max_zoom}
    onchange={(nextValue) => {
      gradio.props.value = nextValue;
      gradio.dispatch("change", nextValue);
    }}
  />
</Block>
