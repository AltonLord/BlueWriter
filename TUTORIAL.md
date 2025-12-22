# BlueWriter Tutorial

## Quick Start Summary

BlueWriter is a writing tool designed to help you organize and write your fiction. Here's how to get started quickly:

1. **Launch the Application**:
   - Open terminal in `/fast/BlueWriter/`
   - Run: `python main.py`

2. **Create Your First Project**:
   - Click "File" → "New Project"
   - Give your project a name (e.g., "My Novel")
   - Click "Create"

3. **Add Your First Story**:
   - In the sidebar, click "New Story"
   - Enter a title for your story (e.g., "Book One")

4. **Create Your First Chapter**:
   - Click on the timeline canvas
   - Click "New Chapter" in the toolbar
   - Edit the chapter title and content

5. **Organize Your Writing**:
   - Drag chapters around the timeline to arrange them
   - Double-click any chapter to edit its content

6. **Save Your Work**:
   - BlueWriter auto-saves every minute, but you can also use Ctrl+S or File → Save

## What Is BlueWriter?

BlueWriter is a desktop application that helps writers organize their stories using a timeline-based approach. Instead of traditional outlining tools, it presents your story as a visual timeline where each chapter becomes a sticky note that you can arrange and move around.

This allows you to:
- See the overall flow of your story
- Move chapters around without rewriting
- Visualize how your story builds up over time
- Keep character information and plot points organized

## Getting Started

### Launching BlueWriter

To start using BlueWriter:

1. Open a terminal window in the `/fast/BlueWriter/` directory
2. Run the command: `python main.py`
3. The application will launch with a main window

### Creating a New Project

1. Click on the "File" menu at the top of the screen
2. Select "New Project"
3. In the dialog that appears:
   - Enter a name for your project (e.g., "My Fantasy Novel")
   - Optionally add a description
   - Click the "Create" button
4. Your new project will open and you'll see the timeline canvas

### Opening an Existing Project

1. Click on the "File" menu
2. Select "Open Project"
3. Choose from the list of previously created projects
4. Click "Open" to load your project

## Working with Stories

### Adding a Story

Once you have a project open:

1. In the sidebar panel (on the left), click the "New Story" button
2. Enter a title for your story (e.g., "Book One")
3. Click "Create"

You can have multiple stories within one project, which is useful for series or multi-part books.

### Switching Between Stories

To work with different stories in your project:

1. In the sidebar panel, select the story you want to work with
2. The timeline canvas will update to show chapters from that story only

## Working with Chapters

### Creating a Chapter

Chapters are represented as sticky notes on the timeline:

1. Click anywhere on the timeline canvas
2. Click the "New Chapter" button in the toolbar (or press Ctrl+Shift+N)
3. A dialog will appear where you can:
   - Set the chapter title
   - Add a brief summary (2-3 sentences)
   - Write the full content of the chapter
   - Choose a color for the sticky note

### Editing a Chapter

To edit an existing chapter:

1. Double-click on any chapter sticky note
2. The chapter editor dialog will open
3. Make your changes to:
   - Title
   - Summary
   - Content
   - Color
4. Click "Save" when finished

### Moving Chapters

You can reorganize your story by dragging chapters:

1. Click and hold on any chapter sticky note
2. Drag it to a new position on the timeline
3. Release the mouse button to drop it in place
4. The chapter's position will be saved automatically

## Using the Timeline Canvas

The main area of BlueWriter is the timeline canvas where your chapters live:

### Navigation

- **Zooming**: 
  - Use mouse wheel to zoom in/out
  - Use View menu: Zoom In, Zoom Out, or Reset Zoom
- **Panning**:
  - Middle-click and drag to pan the view
  - Hold Spacebar + left-click and drag to pan

### Visual Features

- The background shows a subtle sine wave that guides your chapter placement
- Each chapter is shown as a color-coded sticky note
- Notes are arranged along the timeline based on their position

## Chapter Editor Features

When editing chapters, you'll use the rich text editor:

### Basic Text Formatting

The toolbar provides common formatting options:
- **Bold** (Ctrl+B): Make selected text bold
- **Italic** (Ctrl+I): Make selected text italic
- **Underline** (Ctrl+U): Underline selected text
- **Headings**: Change text size for section titles
- **Lists**: Create bullet or numbered lists

### Content Management

The chapter editor has two main sections:
1. **Summary**: A brief 2-3 sentence description shown on the sticky note
2. **Content**: The full chapter text that you can write in

## Keyboard Shortcuts

BlueWriter supports many keyboard shortcuts for efficiency:

| Shortcut | Action |
|----------|--------|
| Ctrl+N | New Project |
| Ctrl+O | Open Project |
| Ctrl+S | Save |
| Ctrl+Z | Undo |
| Ctrl+Y | Redo |
| Ctrl+Shift+N | New Chapter |
| Delete | Delete selected chapter(s) |
| F2 | Rename selected chapter |
| Escape | Deselect all / Close dialog |
| +/- | Zoom in/out |
| Ctrl+0 | Reset zoom |

## Saving and Auto-Save

BlueWriter automatically saves your work every minute:

- Changes are saved to the local database
- You'll see a "*" in the window title when there are unsaved changes
- Use File → Save or Ctrl+S to manually save at any time
- When closing, you'll be prompted to save if there are unsaved changes

## Tips for Effective Writing

1. **Start with broad chapters**: Begin with large chunks of your story and break them down as needed.
2. **Use the timeline**: Think about how your story builds up over time by placing chapters in logical order.
3. **Visualize character interactions**: Use different colors to organize chapters by character focus or scene type.
4. **Experiment with arrangement**: Don't be afraid to move chapters around to find the best flow for your story.

## Troubleshooting

### Common Issues

**Application won't start**
- Make sure you're in the `/fast/BlueWriter/` directory
- Run: `python main.py`
- Check that all required packages are installed with: `pip install -r requirements.txt`

**Chapters not showing up**
- Ensure you have at least one story created in your project
- Try refreshing the view by selecting a different story and back again

**Database connection errors**
- Check that the `/fast/BlueWriter/data/` directory exists and is writable
- If problems persist, try restarting the application

### Getting Help

If you need help:
1. Click "Help" → "About" in the menu bar
2. Use F1 key for keyboard shortcut reference
3. Look for tooltips when hovering over buttons (they provide quick descriptions)

## Conclusion

BlueWriter provides a unique approach to writing fiction by combining the benefits of timeline organization with traditional chapter-based editing. By visualizing your story as a timeline, you can better understand how your plot develops and make adjustments without rewriting large sections of text.

With practice, you'll find that this approach helps you develop more coherent stories while maintaining flexibility in your creative process.
